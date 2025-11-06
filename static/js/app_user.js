// ========================================
// APP_USER.JS - MÓDULO DE USUARIOS
// Sistema de gestión de usuarios con AngularJS
// ========================================

// Función para marcar opción activa en el menú
function activeMenuOption(href) {
    try {
        $(".app-menu .nav-link").removeClass("active").removeAttr('aria-current')
        $(`[href="${(href ? href : "#/")}"]`).addClass("active").attr("aria-current", "page")
    } catch (e) { /* silencio */ }
}

const app = angular.module("angularjsApp", ["ngRoute"])

// ========================================
// CONFIGURACIÓN DE RUTAS
// ========================================
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
        if (!confirm('¿Estás seguro de cerrar sesión?')) {
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
        if (confirm(`¿Estás seguro de eliminar al usuario "${user.nombre}"?\n\nEsta acción no se puede deshacer.`)) {
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
        if (!confirm(`¿Estás seguro de ${accion} a "${user.nombre}"?`)) {
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
        if (!confirm(`¿Desbloquear al usuario "${user.nombre}"?`)) {
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
    // BÚSQUEDA CON DEBOUNCE
    // ========================================
    let searchTimeout
    $scope.$watch('searchText', function(newVal, oldVal) {
        if (newVal !== oldVal) {
            if (searchTimeout) $timeout.cancel(searchTimeout)
            searchTimeout = $timeout(function() {
                loadUsers(false)
            }, 500) // Esperar 500ms después de que el usuario deje de escribir
        }
    })

    // ========================================
    // FILTROS
    // ========================================
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
    // HELPER: BADGE DE ROL
    // ========================================
    $scope.getRolBadge = function(rol_id) {
        switch(parseInt(rol_id)) {
            case 1: return { text: 'Admin', class: 'bg-primary' }
            case 2: return { text: 'Usuario', class: 'bg-success' }
            default: return { text: 'N/A', class: 'bg-secondary' }
        }
    }

    // ========================================
    // HELPER: BADGE DE ESTADO
    // ========================================
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