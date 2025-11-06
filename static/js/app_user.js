
function activeMenuOption(href) {
    try {
        $(".app-menu .nav-link").removeClass("active").removeAttr('aria-current')
        $(`[href="${(href ? href : "#/")}"]`).addClass("active").attr("aria-current", "page")
    } catch (e) { /* silencio */ }
}


const app = angular.module("angularjsApp", ["ngRoute"])


app.config(function ($routeProvider, $locationProvider) {
    $locationProvider.hashPrefix("")

    $routeProvider
    .when("/", {
        templateUrl: "/dashboard",
        controller: "dashboardCtrl"
    })
    .when("/login", {
        templateUrl: "/login",
        controller: "loginCtrl"
    })
    .when("/users", {
        templateUrl: "/users",
        controller: "usersCtrl"
    })
    
 
    .when('/roles', {
        templateUrl: '/roles', 
        controller: 'rolesCtrl' 
    })
     .when('/dispositivos', {
        templateUrl: '/dispositivos', 
        controller: 'dispositivosCtrl' 
    })

        
    .otherwise({
        redirectTo: "/"
    })
})

// ========================================
// CONFIGURACIÓN GLOBAL Y AUTENTICACIÓN
// ========================================
app.run(["$rootScope", "$http", "$location", function($rootScope, $http, $location) {
    $rootScope.currentUser = null
    $rootScope.loggedIn = false

    // Obtener usuario actual
    $rootScope.getCurrentUser = function() {
        return $http.get('/api/user/current')
        .then(function(response) {
            if (response.data.success) {
                $rootScope.currentUser = response.data.user
                $rootScope.loggedIn = true
                return $rootScope.currentUser
            }
            $rootScope.currentUser = null
            $rootScope.loggedIn = false
            return null
        })
        .catch(function() {
            $rootScope.currentUser = null
            $rootScope.loggedIn = false
            return null
        })
    }

    // Cerrar sesión
    $rootScope.logout = function() {
        // [IMPORTANTE]: Reemplazar 'confirm' por un modal personalizado.
        if (!window.confirm('¿Estás seguro de cerrar sesión?')) {
            return
        }

        return $http.post('/api/logout')
        .then(function() {
            $rootScope.currentUser = null
            $rootScope.loggedIn = false
            toast('Sesión cerrada exitosamente', 2)
            setTimeout(function() {
                window.location.hash = "#/login"
                window.location.reload()
            }, 500)
        })
        .catch(function(error) {
            $rootScope.currentUser = null
            $rootScope.loggedIn = false
            toast('Error al cerrar sesión: ' + (error.data?.message || 'Error desconocido'), 3)
            window.location.hash = "#/login"
            window.location.reload()
        })
    }

    // Verificar autenticación en cada cambio de ruta
    $rootScope.$on('$routeChangeStart', function(event, next, current) {
        // Si intenta acceder a una ruta protegida sin estar autenticado
        if (next.$$route && next.$$route.originalPath !== '/login') {
            if (!$rootScope.loggedIn && !$rootScope.currentUser) {
                event.preventDefault()
                $location.path('/login')
            }
        }
    })

    // Cargar usuario actual al iniciar
    $rootScope.getCurrentUser()
}])


// ========================================
// CONTROLLER: LOGIN
// ========================================
app.controller("loginCtrl", function ($scope, $http, $rootScope, $location) {
    $scope.usuario = ""
    $scope.contrasena = ""
    $scope.mensaje = ""
    $scope.cargando = false
    $scope.tipoMensaje = "primary"

    $rootScope.currentUser = null

    // Si ya hay sesión activa, redirigir al dashboard
    $http.get('/api/check-session').then(function(response) {
        if (response.data.success && response.data.logged_in) {
            $rootScope.getCurrentUser().then(function() {
                $location.path('/')
            })
        }
    }).catch(function() {})

    $scope.login = function() {
        if (!$scope.usuario || !$scope.contrasena) {
            $scope.mensaje = "Por favor ingresa usuario y contraseña"
            $scope.tipoMensaje = "warning"
            return
        }

        $scope.cargando = true
        $scope.mensaje = ""

        $http.post('/api/login', {
            usuario: $scope.usuario,
            contrasena: $scope.contrasena
        }).then(function(response) {
            $scope.cargando = false
            if (response.data.success) {
                $scope.mensaje = response.data.message
                $scope.tipoMensaje = "success"
                
                // Recargar usuario y redirigir
                $rootScope.getCurrentUser().finally(function() {
                    toast('Login exitoso. Bienvenido!', 2)
                    setTimeout(function() {
                        $location.path('/')
                        $scope.$apply()
                    }, 500)
                })
            } else {
                $scope.mensaje = response.data.message
                $scope.tipoMensaje = "danger"
            }
        }).catch(function(error) {
            $scope.cargando = false
            $scope.mensaje = (error.data && error.data.message) 
                ? error.data.message 
                : "Error de conexión. Intenta nuevamente."
            $scope.tipoMensaje = "danger"
        })
    }

    // Limpiar mensajes al escribir
    $scope.$watch('usuario', function() { $scope.mensaje = "" })
    $scope.$watch('contrasena', function() { $scope.mensaje = "" })
})

// ========================================
// CONTROLLER: GESTIÓN DE USUARIOS
// ========================================
app.controller("usersCtrl", function ($scope, $http, $rootScope, $timeout) {
    // Inicialización de variables de estado
    $scope.users = []
    $scope.loading = true
    $scope.saving = false
    $scope.editingUser = null
    $scope.formUser = {}
    $scope.searchText = ""
    $scope.filterRol = ""
    $scope.filterActivo = ""
    
    let userModal = null
    
    // ========================================
    // CARGAR USUARIOS
    // ========================================
    function loadUsers(showLoading = true) {
        if (showLoading) $scope.loading = true
        
        // Construir query params para filtros
        let params = {}
        if ($scope.searchText) params.search = $scope.searchText
        if ($scope.filterRol) params.rol_id = $scope.filterRol
        if ($scope.filterActivo !== "") params.activo = $scope.filterActivo
        
        $http.get('/api/users', { 
            params: params,
            withCredentials: true 
        })
        .then(function(response) {
            if (response.data.success) {
                $scope.users = response.data.users
                if (!showLoading) {
                    toast(`${response.data.count} usuarios encontrados`, 2)
                }
            } else {
                toast(response.data.message || 'Error al cargar usuarios', 3)
            }
        })
        .catch(function(error) {
            toast('Error al cargar usuarios: ' + (error.data?.message || error.statusText), 3)
        })
        .finally(function() {
            $scope.loading = false
        })
    }
    
    // ========================================
    // MODAL: CREAR/EDITAR
    // ========================================
    function initModal() {
        const modalEl = document.getElementById('userModal')
        if (modalEl) {
            userModal = new bootstrap.Modal(modalEl)
            
            // Limpiar formulario al cerrar
            modalEl.addEventListener('hidden.bs.modal', function() {
                $scope.$apply(function() {
                    $scope.editingUser = null
                    $scope.formUser = {}
                })
            })
        }
    }
    
    $scope.showCreateModal = function() {
        $scope.editingUser = null
        $scope.formUser = {
            activo: true,
            rol_id: 2
        }
        if (userModal) userModal.show()
    }
    
    $scope.showEditModal = function(user) {
        $scope.editingUser = user
        $scope.formUser = {
            nombre: user.nombre,
            email: user.email,
            rol_id: user.rol_id,
            activo: user.activo,
            password: '' // Vacío para no cambiar
        }
        if (userModal) userModal.show()
    }
    
    // ========================================
    // GUARDAR USUARIO
    // ========================================
    $scope.saveUser = function() {
        if ($scope.saving) return

        // Validaciones básicas
        if (!$scope.formUser.nombre || !$scope.formUser.email) {
            toast('Nombre y email son requeridos', 3)
            return
        }

        if (!$scope.editingUser && !$scope.formUser.password) {
            toast('La contraseña es requerida para nuevos usuarios', 3)
            return
        }

        $scope.saving = true
        let method = $scope.editingUser ? 'PUT' : 'POST'
        let url = $scope.editingUser 
            ? `/api/users/${$scope.editingUser.id}` 
            : '/api/register'

        let payload = angular.copy($scope.formUser) || {}

        if ($scope.editingUser) {
            // Editar: no enviar password si está vacío
            if (!payload.password) {
                delete payload.password
            }
            if (payload.rol_id) payload.rol_id = parseInt(payload.rol_id, 10)
        } else {
            // Crear: mapear a formato esperado
            payload = {
                nombre_usuario: payload.nombre,
                correo_electronico: payload.email,
                contrasena: payload.password,
                rol_id: parseInt(payload.rol_id, 10)
            }
        }

        $http({
            method: method,
            url: url,
            data: payload,
            withCredentials: true,
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) {
            if (response.data && response.data.success) {
                toast(response.data.message || 'Usuario guardado exitosamente', 2)
                if (userModal) userModal.hide()
                loadUsers(false)
            } else {
                toast(response.data?.message || 'Error al guardar usuario', 4)
            }
        })
        .catch(function(error) {
            toast('Error: ' + (error.data?.message || error.statusText || 'Error desconocido'), 5)
        })
        .finally(function() {
            $scope.saving = false
        })
    }
    
    // ========================================
    // ELIMINAR USUARIO
    // ========================================
    $scope.confirmDelete = function(user) {
        // [IMPORTANTE]: Reemplazar 'confirm' por un modal personalizado.
        if (window.confirm(`¿Estás seguro de eliminar al usuario "${user.nombre}"?\n\nEsta acción no se puede deshacer.`)) {
            $http.delete(`/api/users/${user.id}`, { withCredentials: true })
            .then(function(response) {
                if (response.data.success) {
                    toast(response.data.message || 'Usuario eliminado', 2)
                    loadUsers(false)
                } else {
                    toast(response.data.message || 'Error al eliminar usuario', 3)
                }
            })
            .catch(function(error) {
                toast('Error: ' + (error.data?.message || error.statusText), 3)
            })
        }
    }
    
    // ========================================
    // ACTIVAR/DESACTIVAR USUARIO
    // ========================================
    $scope.toggleUserStatus = function(user) {
        const accion = user.activo ? 'desactivar' : 'activar'
        // [IMPORTANTE]: Reemplazar 'confirm' por un modal personalizado.
        if (!window.confirm(`¿Estás seguro de ${accion} a "${user.nombre}"?`)) {
            return
        }

        $http.patch(`/api/users/${user.id}/toggle-active`, {}, { withCredentials: true })
        .then(function(response) {
            if (response.data.success) {
                toast(response.data.message, 2)
                user.activo = response.data.activo
            } else {
                toast(response.data.message || 'Error al cambiar estado', 3)
            }
        })
        .catch(function(error) {
            toast('Error: ' + (error.data?.message || error.statusText), 3)
        })
    }

    // ========================================
    // DESBLOQUEAR USUARIO
    // ========================================
    $scope.unlockUser = function(user) {
        // [IMPORTANTE]: Reemplazar 'confirm' por un modal personalizado.
        if (!window.confirm(`¿Desbloquear al usuario "${user.nombre}"?"`)) {
            return
        }

        $http.patch(`/api/users/${user.id}/unlock`, {}, { withCredentials: true })
        .then(function(response) {
            if (response.data.success) {
                toast(response.data.message, 2)
                loadUsers(false)
            } else {
                toast(response.data.message || 'Error al desbloquear', 3)
            }
        })
        .catch(function(error) {
            toast('Error: ' + (error.data?.message || error.statusText), 3)
        })
    }

    // ========================================
    // BÚSQUEDA Y FILTROS
    // ========================================
    let searchTimeout
    $scope.$watch('searchText', function(newVal, oldVal) {
        if (newVal !== oldVal) {
            if (searchTimeout) $timeout.cancel(searchTimeout)
            searchTimeout = $timeout(function() {
                loadUsers(false)
            }, 500)
        }
    })

    $scope.applyFilters = function() {
        loadUsers(false)
    }

    $scope.clearFilters = function() {
        $scope.searchText = ""
        $scope.filterRol = ""
        $scope.filterActivo = ""
        loadUsers(false)
    }

    // ========================================
    // HELPER: BADGE DE ROL Y ESTADO
    // ========================================
    $scope.getRolBadge = function(rol_id) {
        switch(parseInt(rol_id)) {
            case 1: return { text: 'Admin', class: 'bg-primary' }
            case 2: return { text: 'Usuario', class: 'bg-success' }
            default: return { text: 'N/A', class: 'bg-secondary' }
        }
    }

    $scope.getEstadoBadge = function(activo) {
        return activo 
            ? { text: 'Activo', class: 'bg-success' }
            : { text: 'Inactivo', class: 'bg-danger' }
    }
    
    // ========================================
    // INICIALIZACIÓN
    // ========================================
    initModal()
    loadUsers()
    activeMenuOption("#/users")
})

// ========================================
// CONTROLLER: GESTIÓN DE ROLES
// ========================================
app.controller("rolesCtrl", function ($scope, $http, $rootScope, $timeout) {
    $scope.roles = []
    $scope.loading = true
    $scope.saving = false
    $scope.editingRole = null
    // Nuevo estado para la eliminación
    $scope.deletingRole = null 
    $scope.formRole = {
        nombre: '',
        descripcion: ''
    }
    // Mensajes de estado para el formulario de rol de creación
    $scope.successMessage = null
    $scope.errorMessage = null
    $scope.isLoading = false // Usado para el botón de "Crear Rol"
    
    let roleModal = null
    let deleteModal = null // Nuevo modal para confirmación de borrado
    
    // Función para limpiar mensajes
    function clearMessages() {
        $scope.successMessage = null
        $scope.errorMessage = null
    }

    // ========================================
    // CARGAR ROLES (GET /api/roles)
    // ========================================
    function loadRoles(showLoading = true) {
        if (showLoading) $scope.loading = true
        
        $http.get('/api/roles', { withCredentials: true })
        .then(function(response) {
            if (response.data.success) {
                // Tu API devuelve 'data' en el JSON, lo cual es correcto
                $scope.roles = response.data.data 
            } else {
                toast(response.data.message || 'Error al cargar roles', 3)
            }
        })
        .catch(function(error) {
            toast('Error de conexión al cargar roles: ' + (error.data?.message || error.statusText), 3)
        })
        .finally(function() {
            $scope.loading = false
        })
    }
    
    // ========================================
    // CREAR ROL (POST /api/roles)
    // ========================================
    $scope.addRole = function() {
        if ($scope.isLoading) return
        clearMessages()

        if (!$scope.formRole.nombre || $scope.formRole.nombre.length > 50) {
            $scope.errorMessage = 'El nombre del rol es requerido (máx 50 caracteres).'
            return
        }

        $scope.isLoading = true
        
        let payload = {
            nombre: $scope.formRole.nombre,
            descripcion: $scope.formRole.descripcion
        }

        $http.post('/api/roles', payload, {
            withCredentials: true,
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) {
            if (response.data && response.data.success) {
                $scope.successMessage = response.data.message || `Rol '${payload.nombre}' creado.`
                // Limpiar formulario y recargar lista
                $scope.formRole = { nombre: '', descripcion: '' }
                loadRoles(false)
            } else {
                $scope.errorMessage = response.data?.message || 'Error al crear rol. Intenta nuevamente.'
            }
        })
        .catch(function(error) {
            $scope.errorMessage = 'Error de conexión: ' + (error.data?.message || error.statusText || 'Error desconocido')
        })
        .finally(function() {
            $scope.isLoading = false
        })
    }

    // ========================================
    // MODAL: INICIALIZACIÓN EDICIÓN
    // ========================================
    function initEditModal() {
        const modalEl = document.getElementById('roleModal') 
        if (modalEl) {
            // Inicializar el modal de Bootstrap
            roleModal = new bootstrap.Modal(modalEl)
            
            // Limpiar datos del formulario al cerrar el modal
            modalEl.addEventListener('hidden.bs.modal', function() {
                $scope.$apply(function() {
                    $scope.editingRole = null
                    $scope.formRole = { nombre: '', descripcion: '' }
                })
            })
        }
    }

    // ========================================
    // MODAL: INICIALIZACIÓN ELIMINACIÓN
    // ========================================
    function initDeleteModal() {
        const modalEl = document.getElementById('deleteRoleModal') 
        if (modalEl) {
            deleteModal = new bootstrap.Modal(modalEl)
            
            // Limpiar estado al cerrar el modal
            modalEl.addEventListener('hidden.bs.modal', function() {
                $scope.$apply(function() {
                    $scope.deletingRole = null
                })
            })
        }
    }
    
    $scope.showEditModal = function(role) {
        clearMessages() // FIX: Limpiar mensajes de creación
        $scope.editingRole = role
        // Usar angular.copy para evitar modificar la fila de la tabla antes de guardar
        $scope.formRole = angular.copy(role)
        if (roleModal) roleModal.show()
    }
    
    // ========================================
    // GUARDAR ROL (PUT /api/roles/:id)
    // ========================================
    $scope.saveRole = function() {
        if ($scope.saving) return

        if (!$scope.formRole.nombre || $scope.formRole.nombre.length > 50) {
            toast('El nombre del rol es requerido (máx 50 caracteres)', 3)
            return
        }

        $scope.saving = true
        let url = `/api/roles/${$scope.editingRole.id}` 

        let payload = {
            nombre: $scope.formRole.nombre,
            descripcion: $scope.formRole.descripcion
        }

        $http.put(url, payload, {
            withCredentials: true,
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) {
            if (response.data && response.data.success) {
                toast(response.data.message || 'Rol actualizado exitosamente', 2)
                if (roleModal) roleModal.hide()
                loadRoles(false)
            } else {
                toast(response.data?.message || 'Error al actualizar rol', 4)
            }
        })
        .catch(function(error) {
            toast('Error: ' + (error.data?.message || error.statusText || 'Error desconocido'), 5)
        })
        .finally(function() {
            $scope.saving = false
        })
    }
    
    // ========================================
    // ELIMINAR ROL (DELETE /api/roles/:id) - PASO 1: CONFIRMACIÓN
    // ========================================
    $scope.confirmDelete = function(role) {
        // FIX: Reemplazando 'confirm' por un modal personalizado.
        $scope.deletingRole = role
        if (deleteModal) deleteModal.show()
    }

    // ========================================
    // ELIMINAR ROL (DELETE /api/roles/:id) - PASO 2: EJECUCIÓN
    // ========================================
    $scope.deleteRoleConfirmed = function() {
        if (!$scope.deletingRole || $scope.saving) return
        
        $scope.saving = true // Usamos 'saving' para el spinner
        let roleToDelete = angular.copy($scope.deletingRole)

        $http.delete(`/api/roles/${roleToDelete.id}`, { withCredentials: true })
        .then(function(response) {
            if (response.data.success) {
                toast(response.data.message || `Rol ${roleToDelete.nombre} eliminado.`, 2)
                if (deleteModal) deleteModal.hide()
                loadRoles(false) // Recargar la lista
            } else {
                toast(response.data.message || 'Error al eliminar rol', 3)
            }
        })
        .catch(function(error) {
            toast('Error: ' + (error.data?.message || error.statusText), 3)
        })
        .finally(function() {
            $scope.saving = false
        })
    }
    
    // ========================================
    // INICIALIZACIÓN
    // ========================================
    initEditModal() // Inicializa el modal de edición
    initDeleteModal() // Inicializa el modal de eliminación
    loadRoles()
    activeMenuOption("#/roles")
})

app.controller("dispositivosCtrl", function ($scope, $http, $rootScope, $location) {
  
})




// ========================================
// CONTROLLER: DASHBOARD
// ========================================
app.controller("dashboardCtrl", function ($scope, $http, $rootScope, $location) {
    $scope.currentUser = null
    $scope.loading = true

    $rootScope.getCurrentUser().then(function(user) {
        $scope.currentUser = user || null
        if (!$scope.currentUser) {
            $location.path('/login')
            return
        }
    }).finally(function() {
        $scope.loading = false
        activeMenuOption("#/")
    })

    $scope.goToLogin = function() {
        $location.path('/login')
    }
})

// ========================================
// FILTRO: TRUSTED HTML
// ========================================
app.filter('trusted', ['$sce', function($sce) {
    return function(text) {
        return $sce.trustAsHtml(text)
    }
}])

// ========================================
// FIN DEL MÓDULO
// ========================================
