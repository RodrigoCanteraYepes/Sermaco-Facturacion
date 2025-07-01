# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductCategoria(models.Model):
    _name = 'product.categoria'
    _description = 'Categorías de Productos para Ofertas'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre de Categoría',
        required=True,
        translate=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de aparición en las vistas'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único para identificar la categoría'
    )
    
    description = fields.Text(
        string='Descripción',
        translate=True
    )
    
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color para mostrar en las vistas kanban'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Relación con productos
    product_ids = fields.One2many(
        'product.template',
        'categoria_oferta_id',
        string='Productos'
    )
    
    product_count = fields.Integer(
        string='Número de Productos',
        compute='_compute_product_count'
    )
    
    @api.depends('product_ids')
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.product_ids)
    
    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("El código '%s' ya existe. Debe ser único.") % record.code)
    
    def action_view_products(self):
        """Acción para ver los productos de esta categoría"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Productos - %s') % self.name,
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [('categoria_oferta_id', '=', self.id)],
            'context': {
                'default_categoria_oferta_id': self.id,
                'search_default_categoria_oferta_id': self.id,
            }
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    categoria_oferta_id = fields.Many2one(
        'product.categoria',
        string='Categoría de Oferta',
        help='Categoría para filtrado en ofertas (Precio, Alquiler, Montaje, etc.)'
    )
    
    # Campos específicos para ofertas
    es_alquiler = fields.Boolean(
        string='Es Alquiler',
        default=False,
        help='Indica si este producto es para alquiler'
    )
    
    precio_alquiler_diario = fields.Float(
        string='Precio Alquiler Diario',
        help='Precio por día de alquiler'
    )
    
    precio_alquiler_mensual = fields.Float(
        string='Precio Alquiler Mensual',
        help='Precio por mes de alquiler'
    )
    
    es_montaje = fields.Boolean(
        string='Es Montaje',
        default=False,
        help='Indica si este producto es un servicio de montaje'
    )
    
    es_porte = fields.Boolean(
        string='Es Porte',
        default=False,
        help='Indica si este producto es un servicio de transporte/porte'
    )
    
    precio_porte_km = fields.Float(
        string='Precio por Km',
        help='Precio por kilómetro para servicios de porte'
    )
    
    distancia_minima = fields.Float(
        string='Distancia Mínima (Km)',
        help='Distancia mínima facturable para portes'
    )
    
    # Campos para búsqueda y filtrado
    tags_busqueda = fields.Char(
        string='Tags de Búsqueda',
        help='Palabras clave separadas por comas para facilitar la búsqueda'
    )
    
    especificaciones_tecnicas = fields.Html(
        string='Especificaciones Técnicas',
        help='Detalles técnicos del producto para mostrar en ofertas'
    )