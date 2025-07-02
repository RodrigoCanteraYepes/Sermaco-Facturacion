{
    'name': 'Gestión de Ofertas - Etapa Ofertando',
    'version': '18.0.1.0.2.0',
    'category': 'Sales',
    'summary': 'Módulo para gestión automatizada de ofertas en proceso de ventas',
    'description': """
        Gestión de Ofertas - Etapa Ofertando
        ====================================
        
        Este módulo permite la gestión automatizada de ofertas en el proceso de ventas.
        
        Características principales:
        * Creación de ofertas tipo Proyectos y Venta directa
        * Gestión de capítulos por oferta
        * Sistema de cláusulas generales y específicas
        * Delegación de responsabilidades
        * Gestión de tarifas por producto
        * Validaciones automáticas de integridad
        * Automatizaciones basadas en oportunidades calificadas
        * Integración completa con CRM y Ventas
        * Reportes y análisis avanzados
    """,
    'author': 'Sermaco',
    'website': 'https://www.sermaco.com',
    'depends': [
        'base',
        'crm',
        'sale_management',
        'product',
        'project',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/product_categoria_data.xml',
        'views/oferta_views.xml',
        'views/oferta_capitulo_views.xml',
        'views/oferta_clausula_views.xml',
        'views/oferta_tarifa_views.xml',
        'views/oferta_delegacion_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/product_categoria_views.xml',
        'views/product_selector_wizard_views.xml',
        'views/ventas_filtrado_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}