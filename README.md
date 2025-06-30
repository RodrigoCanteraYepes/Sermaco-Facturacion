# Módulo Gestión de Ofertas - Etapa OFERTANDO

## 📋 Descripción

Módulo completo para Odoo 18 que gestiona el proceso de creación y administración de ofertas comerciales en la etapa de "OFERTANDO". Permite crear ofertas estructuradas con capítulos, tarifas, cláusulas y delegaciones, integrándose perfectamente con los módulos CRM y Ventas de Odoo.

## 🚀 Características Principales

### ✨ Gestión de Ofertas
- **Dos tipos de ofertas**: Proyectos y Venta Directa
- **Estados del flujo**: Borrador → Revisión → Aprobada → Enviada → Aceptada/Rechazada
- **Numeración automática** con secuencias configurables
- **Validación de integridad** antes de envío
- **Cálculo automático** de montos y márgenes

### 📚 Sistema de Capítulos
- **Organización por capítulos** (solo para proyectos)
- **Asignación de productos** por capítulo
- **Generación automática** de cláusulas específicas
- **Duplicación** de capítulos para reutilización
- **Validación** de productos sin precio

### 💰 Gestión de Tarifas
- **Precios por producto** con fechas de validez
- **Descuentos** por porcentaje y monto fijo
- **Márgenes automáticos** calculados
- **Aplicación de descuentos** por volumen
- **Extensión de validez** mediante wizard
- **Tarifas automáticas** basadas en listas de precios

### 📝 Sistema de Cláusulas
- **Cláusulas generales y específicas**
- **Aplicación automática** según tipo de oferta
- **Filtros por sector, país, monto**
- **Gestión de fechas** de vigencia
- **Cláusulas obligatorias** configurables

### 👥 Gestión de Delegaciones
- **Asignación de responsabilidades**
- **Estados de seguimiento**: Pendiente → Aceptada → En Progreso → Completada
- **Notificaciones automáticas** de vencimiento
- **Reasignación** y extensión de plazos
- **Delegaciones obligatorias** por monto

### 🔗 Integración CRM
- **Extensión de oportunidades** (crm.lead)
- **Generación automática** de ofertas
- **Validación de requerimientos**
- **Configuración de tipo** de oferta preferido
- **Productos requeridos** y presupuestos

### 🛒 Integración Ventas
- **Extensión de órdenes** de venta (sale.order)
- **Trazabilidad** de oferta origen
- **Sincronización** de cambios
- **Reporte comparativo** oferta vs orden
- **Aplicación automática** de condiciones

## 📦 Estructura del Módulo

```
gestion_ofertas_etapa_ofertando/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── oferta.py                 # Modelo principal de ofertas
│   ├── oferta_capitulo.py        # Gestión de capítulos
│   ├── oferta_clausula.py        # Sistema de cláusulas
│   ├── oferta_tarifa.py          # Gestión de tarifas
│   ├── oferta_delegacion.py      # Sistema de delegaciones
│   ├── crm_lead.py              # Extensión CRM
│   └── sale_order.py            # Extensión Ventas
├── views/
│   ├── oferta_views.xml         # Vistas principales
│   ├── oferta_capitulo_views.xml
│   ├── oferta_clausula_views.xml
│   ├── oferta_tarifa_views.xml
│   ├── oferta_delegacion_views.xml
│   ├── crm_lead_views.xml       # Extensión vistas CRM
│   ├── sale_order_views.xml     # Extensión vistas Ventas
│   └── menu.xml                 # Estructura de menús
├── security/
│   ├── ir.model.access.csv      # Permisos de acceso
│   └── security.xml             # Grupos y reglas
├── data/
│   └── data.xml                 # Datos iniciales
└── README.md
```

## 🛠️ Instalación

1. **Copiar el módulo** en el directorio de addons de Odoo 18
2. **Actualizar la lista** de aplicaciones
3. **Instalar el módulo** "Gestión de Ofertas - Etapa OFERTANDO"
4. **Configurar permisos** de usuario según roles

## 👤 Roles y Permisos

### 🔵 Usuario de Ofertas
- Crear y editar sus propias ofertas
- Ver ofertas de otros usuarios (solo lectura)
- Gestionar capítulos, tarifas y delegaciones

### 🟡 Gestor de Ofertas
- Acceso completo a todas las ofertas
- Aprobar ofertas en revisión
- Configurar cláusulas y parámetros
- Gestionar delegaciones de equipo

### 🟢 Aprobador de Ofertas
- Aprobar ofertas que requieren autorización
- Acceso a reportes y análisis
- Supervisar delegaciones críticas

## ⚙️ Configuración

### Parámetros del Sistema
- **Días de vencimiento**: 30 días por defecto
- **Margen mínimo**: 15% por defecto
- **Monto para delegación obligatoria**: $25,000
- **Generación automática**: Habilitada
- **Límite de delegaciones por usuario**: 10

### Secuencias
- **Numeración de ofertas**: OF000001, OF000002...
- **Prefijo personalizable**
- **Incremento automático**

## 🔄 Flujo de Trabajo

### 1. Creación de Oferta
```
Oportunidad Calificada → Oferta Borrador → Agregar Capítulos → Asignar Productos → Definir Tarifas → Aplicar Cláusulas → Crear Delegaciones
```

### 2. Aprobación
```
Borrador → Enviar a Revisión → Aprobar → Enviar a Cliente → Aceptar/Rechazar
```

### 3. Conversión a Venta
```
Oferta Aceptada → Crear Orden de Venta → Sincronizar Condiciones → Seguimiento
```

## 📊 Reportes y Análisis

### Reportes Disponibles
- **Ofertas por Estado**: Análisis de distribución
- **Ofertas por Tipo**: Proyectos vs Venta Directa
- **Análisis de Tarifas**: Márgenes y precios
- **Delegaciones**: Estado y cumplimiento

### Vistas Analíticas
- **Pivot**: Análisis multidimensional
- **Gráficos**: Visualización de tendencias
- **Kanban**: Vista de tablero
- **Calendario**: Seguimiento de fechas

## 🔧 Automatizaciones

### Triggers Automáticos
- **Oportunidad calificada** → Crear oferta borrador
- **Selección de tipo** → Activar/desactivar capítulos
- **Agregar producto** → Crear tarifa automática
- **Monto alto** → Crear delegación obligatoria
- **Vencimiento próximo** → Notificación automática

### Validaciones
- **Integridad de oferta** antes de envío
- **Productos sin precio** → Bloqueo
- **Capítulos vacíos** → Advertencia
- **Delegaciones pendientes** → Alerta

## 🎯 Casos de Uso

### Caso 1: Oferta de Proyecto
1. Técnico comercial recibe oportunidad calificada
2. Sistema crea oferta borrador automáticamente
3. Se crean capítulos por categoría de producto
4. Se asignan productos y tarifas por capítulo
5. Se aplican cláusulas específicas de proyecto
6. Se crea delegación para ingeniería (si monto > $25K)
7. Se envía a revisión y aprobación
8. Se envía al cliente

### Caso 2: Venta Directa
1. Oportunidad simple de productos estándar
2. Oferta sin capítulos, directa
3. Tarifas de lista de precios
4. Cláusulas generales automáticas
5. Aprobación rápida
6. Envío inmediato

## 🔍 Validaciones y Controles

### Validaciones de Negocio
- ✅ **Productos con precio**: Obligatorio antes de envío
- ✅ **Capítulos con productos**: Para ofertas de proyecto
- ✅ **Fechas de validez**: Coherencia temporal
- ✅ **Márgenes mínimos**: Según configuración
- ✅ **Delegaciones obligatorias**: Por monto

### Controles de Acceso
- 🔒 **Usuarios propios**: Solo sus ofertas
- 🔒 **Gestores**: Acceso completo
- 🔒 **Estados**: Transiciones controladas
- 🔒 **Aprobaciones**: Según jerarquía

## 🚨 Alertas y Notificaciones

### Alertas Visuales
- 🔴 **Productos sin precio**
- 🟡 **Delegaciones vencidas**
- 🔵 **Ofertas por vencer**
- 🟢 **Integridad completa**

### Notificaciones Automáticas
- 📧 **Delegación asignada**
- 📧 **Delegación por vencer**
- 📧 **Oferta aprobada**
- 📧 **Oferta vencida**

## 🔄 Integraciones

### Módulos Odoo
- **CRM**: Oportunidades y clientes
- **Sales**: Órdenes de venta
- **Product**: Catálogo de productos
- **Account**: Monedas y precios
- **Project**: Gestión de proyectos (futuro)

### APIs Externas
- Preparado para integración con sistemas externos
- Estructura modular para extensiones

## 📈 Métricas y KPIs

### Indicadores Clave
- **Tiempo promedio**: Oportunidad → Oferta
- **Tasa de conversión**: Ofertas → Ventas
- **Margen promedio**: Por tipo de oferta
- **Cumplimiento**: Delegaciones a tiempo
- **Efectividad**: Ofertas aceptadas vs enviadas

## 🛡️ Seguridad

### Mejores Prácticas
- **Encriptación** de datos sensibles
- **Auditoría** de cambios
- **Backup** automático
- **Acceso controlado** por roles
- **Validación** de entrada de datos

## 🔮 Roadmap Futuro

### Versión 2.0
- [ ] Integración con módulo Project
- [ ] Workflow avanzado con aprobaciones múltiples
- [ ] Templates de ofertas por industria
- [ ] Integración con firma electrónica
- [ ] Dashboard ejecutivo
- [ ] Análisis predictivo de conversión
- [ ] Integración con WhatsApp/Email
- [ ] Generación automática de documentos PDF

## 📞 Soporte

Para soporte técnico o consultas sobre el módulo:
- **Documentación**: Este README
- **Issues**: Reportar en el repositorio
- **Comunidad**: Foros de Odoo

## 📄 Licencia

Este módulo está licenciado bajo LGPL-3.0, compatible con Odoo Community Edition.

---

**Desarrollado para Odoo 18** | **Versión 1.0** | **2024**