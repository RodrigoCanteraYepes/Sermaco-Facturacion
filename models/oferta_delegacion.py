# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class OfertaDelegacion(models.Model):
    _name = 'oferta.delegacion'
    _description = 'Delegación de Ofertas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_delegacion desc'
    _rec_name = 'display_name'

    # Campos básicos
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    # Relaciones
    oferta_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta',
        required=True,
        ondelete='cascade'
    )
    
    usuario_delegado_id = fields.Many2one(
        'res.users',
        string='Usuario Delegado',
        required=True,
        tracking=True
    )
    
    usuario_delegante_id = fields.Many2one(
        'res.users',
        string='Usuario Delegante',
        default=lambda self: self.env.user,
        required=True,
        readonly=True
    )
    
    # Campos de fechas
    fecha_delegacion = fields.Datetime(
        string='Fecha de Delegación',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    
    fecha_limite = fields.Date(
        string='Fecha Límite',
        required=True
    )
    
    fecha_aceptacion = fields.Datetime(
        string='Fecha de Aceptación',
        readonly=True
    )
    
    fecha_completado = fields.Datetime(
        string='Fecha de Completado',
        readonly=True
    )
    
    # Campos de estado
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='pendiente', tracking=True)
    
    prioridad = fields.Selection([
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ], string='Prioridad', default='normal', tracking=True)
    
    # Campos de tipo y responsabilidad
    tipo_delegacion = fields.Selection([
        ('revision_tecnica', 'Revisión Técnica'),
        ('aprobacion_comercial', 'Aprobación Comercial'),
        ('validacion_precios', 'Validación de Precios'),
        ('revision_legal', 'Revisión Legal'),
        ('aprobacion_gerencial', 'Aprobación Gerencial'),
        ('otro', 'Otro')
    ], string='Tipo de Delegación', required=True)
    
    area_responsable = fields.Selection([
        ('comercial', 'Comercial'),
        ('tecnica', 'Técnica'),
        ('legal', 'Legal'),
        ('financiera', 'Financiera'),
        ('gerencia', 'Gerencia'),
        ('direccion', 'Dirección')
    ], string='Área Responsable')
    
    # Campos de texto
    motivo_delegacion = fields.Text(
        string='Motivo de la Delegación',
        required=True
    )
    
    observaciones_delegante = fields.Text(
        string='Observaciones del Delegante'
    )
    
    observaciones_delegado = fields.Text(
        string='Observaciones del Delegado',
        tracking=True
    )
    
    instrucciones_especiales = fields.Html(
        string='Instrucciones Especiales'
    )
    
    resultado_delegacion = fields.Html(
        string='Resultado de la Delegación'
    )
    
    # Campos de configuración
    requiere_aprobacion = fields.Boolean(
        string='Requiere Aprobación',
        default=False
    )
    
    es_obligatoria = fields.Boolean(
        string='Es Obligatoria',
        default=False,
        help='Si está marcada, la oferta no puede continuar sin completar esta delegación'
    )
    
    notificar_vencimiento = fields.Boolean(
        string='Notificar Vencimiento',
        default=True
    )
    
    dias_notificacion = fields.Integer(
        string='Días de Notificación',
        default=2,
        help='Días antes del vencimiento para enviar notificación'
    )
    
    # Campos computados
    dias_restantes = fields.Integer(
        string='Días Restantes',
        compute='_compute_dias_restantes'
    )
    
    esta_vencida = fields.Boolean(
        string='Está Vencida',
        compute='_compute_esta_vencida'
    )
    
    duracion_delegacion = fields.Integer(
        string='Duración (días)',
        compute='_compute_duracion_delegacion'
    )
    
    puede_aceptar = fields.Boolean(
        string='Puede Aceptar',
        compute='_compute_puede_aceptar'
    )
    
    puede_completar = fields.Boolean(
        string='Puede Completar',
        compute='_compute_puede_completar'
    )
    
    # Campos de seguimiento
    tiempo_respuesta = fields.Float(
        string='Tiempo de Respuesta (horas)',
        compute='_compute_tiempo_respuesta',
        help='Tiempo transcurrido desde la delegación hasta la aceptación'
    )
    
    tiempo_completado = fields.Float(
        string='Tiempo de Completado (horas)',
        compute='_compute_tiempo_completado',
        help='Tiempo transcurrido desde la aceptación hasta la finalización'
    )
    
    @api.depends('usuario_delegado_id', 'tipo_delegacion')
    def _compute_display_name(self):
        for record in self:
            if record.usuario_delegado_id and record.tipo_delegacion:
                record.display_name = f'{dict(record._fields["tipo_delegacion"].selection)[record.tipo_delegacion]} - {record.usuario_delegado_id.name}'
            else:
                record.display_name = _('Nueva Delegación')
    
    @api.depends('fecha_limite')
    def _compute_dias_restantes(self):
        hoy = fields.Date.today()
        for record in self:
            if record.fecha_limite:
                delta = record.fecha_limite - hoy
                record.dias_restantes = delta.days
            else:
                record.dias_restantes = 0
    
    @api.depends('fecha_limite', 'estado')
    def _compute_esta_vencida(self):
        hoy = fields.Date.today()
        for record in self:
            record.esta_vencida = (
                record.fecha_limite < hoy and 
                record.estado not in ['completada', 'cancelada']
            )
    
    @api.depends('fecha_delegacion', 'fecha_limite')
    def _compute_duracion_delegacion(self):
        for record in self:
            if record.fecha_delegacion and record.fecha_limite:
                fecha_delegacion_date = record.fecha_delegacion.date()
                delta = record.fecha_limite - fecha_delegacion_date
                record.duracion_delegacion = delta.days
            else:
                record.duracion_delegacion = 0
    
    @api.depends('usuario_delegado_id', 'estado')
    def _compute_puede_aceptar(self):
        for record in self:
            record.puede_aceptar = (
                record.usuario_delegado_id.id == self.env.user.id and
                record.estado == 'pendiente'
            )
    
    @api.depends('usuario_delegado_id', 'estado')
    def _compute_puede_completar(self):
        for record in self:
            record.puede_completar = (
                record.usuario_delegado_id.id == self.env.user.id and
                record.estado in ['aceptada', 'en_progreso']
            )
    
    @api.depends('fecha_delegacion', 'fecha_aceptacion')
    def _compute_tiempo_respuesta(self):
        for record in self:
            if record.fecha_delegacion and record.fecha_aceptacion:
                delta = record.fecha_aceptacion - record.fecha_delegacion
                record.tiempo_respuesta = delta.total_seconds() / 3600  # Convertir a horas
            else:
                record.tiempo_respuesta = 0.0
    
    @api.depends('fecha_aceptacion', 'fecha_completado')
    def _compute_tiempo_completado(self):
        for record in self:
            if record.fecha_aceptacion and record.fecha_completado:
                delta = record.fecha_completado - record.fecha_aceptacion
                record.tiempo_completado = delta.total_seconds() / 3600  # Convertir a horas
            else:
                record.tiempo_completado = 0.0
    
    @api.constrains('fecha_limite', 'fecha_delegacion')
    def _check_fecha_limite(self):
        for record in self:
            if record.fecha_limite:
                fecha_delegacion_date = record.fecha_delegacion.date()
                if record.fecha_limite <= fecha_delegacion_date:
                    raise ValidationError(
                        _('La fecha límite debe ser posterior a la fecha de delegación.')
                    )
    
    @api.constrains('usuario_delegado_id', 'usuario_delegante_id')
    def _check_usuarios_diferentes(self):
        for record in self:
            if record.usuario_delegado_id.id == record.usuario_delegante_id.id:
                raise ValidationError(
                    _('El usuario delegado no puede ser el mismo que el delegante.')
                )
    
    def action_aceptar_delegacion(self):
        """Acepta la delegación"""
        self.ensure_one()
        if not self.puede_aceptar:
            raise UserError(_('No tiene permisos para aceptar esta delegación.'))
        
        self.write({
            'estado': 'aceptada',
            'fecha_aceptacion': fields.Datetime.now()
        })
        
        # Enviar notificación al delegante
        self.message_post(
            body=_('Delegación aceptada por %s') % self.env.user.name,
            partner_ids=[self.usuario_delegante_id.partner_id.id]
        )
        
        # Crear actividad de seguimiento
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=self.fecha_limite,
            summary=f'Completar delegación: {self.tipo_delegacion}',
            user_id=self.usuario_delegado_id.id
        )
    
    def action_iniciar_progreso(self):
        """Inicia el progreso de la delegación"""
        self.ensure_one()
        if self.estado != 'aceptada':
            raise UserError(_('Solo se puede iniciar el progreso de delegaciones aceptadas.'))
        
        self.estado = 'en_progreso'
        self.message_post(
            body=_('Delegación iniciada por %s') % self.env.user.name
        )
    
    def action_completar_delegacion(self):
        """Completa la delegación"""
        self.ensure_one()
        if not self.puede_completar:
            raise UserError(_('No tiene permisos para completar esta delegación.'))
        
        if not self.observaciones_delegado:
            raise UserError(
                _('Debe agregar observaciones antes de completar la delegación.')
            )
        
        self.write({
            'estado': 'completada',
            'fecha_completado': fields.Datetime.now()
        })
        
        # Enviar notificación al delegante
        self.message_post(
            body=_('Delegación completada por %s') % self.env.user.name,
            partner_ids=[self.usuario_delegante_id.partner_id.id]
        )
        
        # Marcar actividades como completadas
        actividades = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.usuario_delegado_id.id)
        ])
        actividades.action_done()
        
        # Verificar si la oferta puede continuar
        self.oferta_id._verificar_delegaciones_completadas()
    
    def action_rechazar_delegacion(self):
        """Rechaza la delegación"""
        self.ensure_one()
        if self.estado != 'pendiente':
            raise UserError(_('Solo se pueden rechazar delegaciones pendientes.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rechazar Delegación'),
            'res_model': 'oferta.delegacion.rechazar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_delegacion_id': self.id,
            }
        }
    
    def action_cancelar_delegacion(self):
        """Cancela la delegación"""
        self.ensure_one()
        if self.estado in ['completada']:
            raise UserError(_('No se puede cancelar una delegación completada.'))
        
        self.estado = 'cancelada'
        self.message_post(
            body=_('Delegación cancelada por %s') % self.env.user.name
        )
        
        # Cancelar actividades pendientes
        actividades = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)
        ])
        actividades.unlink()
    
    def action_reasignar_delegacion(self):
        """Reasigna la delegación a otro usuario"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reasignar Delegación'),
            'res_model': 'oferta.delegacion.reasignar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_delegacion_id': self.id,
                'default_usuario_actual_id': self.usuario_delegado_id.id,
            }
        }
    
    def action_extender_plazo(self):
        """Extiende el plazo de la delegación"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extender Plazo'),
            'res_model': 'oferta.delegacion.extender.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_delegacion_id': self.id,
                'default_fecha_limite_actual': self.fecha_limite,
            }
        }
    
    # Alias para compatibilidad con vistas
    def action_aceptar(self):
        """Alias para action_aceptar_delegacion"""
        return self.action_aceptar_delegacion()
    
    def action_completar(self):
        """Alias para action_completar_delegacion"""
        return self.action_completar_delegacion()
    
    def action_rechazar(self):
        """Alias para action_rechazar_delegacion"""
        return self.action_rechazar_delegacion()
    
    def action_cancelar(self):
        """Alias para action_cancelar_delegacion"""
        return self.action_cancelar_delegacion()
    
    def action_reasignar(self):
        """Alias para action_reasignar_delegacion"""
        return self.action_reasignar_delegacion()
    
    @api.model
    def _cron_notificar_vencimientos(self):
        """Cron job para notificar delegaciones próximas a vencer"""
        fecha_limite = fields.Date.today() + timedelta(days=2)
        
        delegaciones_por_vencer = self.search([
            ('estado', 'in', ['pendiente', 'aceptada', 'en_progreso']),
            ('fecha_limite', '<=', fecha_limite),
            ('notificar_vencimiento', '=', True)
        ])
        
        for delegacion in delegaciones_por_vencer:
            # Enviar notificación al delegado
            delegacion.activity_schedule(
                'mail.mail_activity_data_warning',
                date_deadline=delegacion.fecha_limite,
                summary=f'Delegación próxima a vencer: {delegacion.tipo_delegacion}',
                note=f'La delegación "{delegacion.display_name}" vence el {delegacion.fecha_limite}',
                user_id=delegacion.usuario_delegado_id.id
            )
            
            # Enviar notificación al delegante
            delegacion.activity_schedule(
                'mail.mail_activity_data_warning',
                date_deadline=delegacion.fecha_limite,
                summary=f'Delegación próxima a vencer: {delegacion.tipo_delegacion}',
                note=f'La delegación "{delegacion.display_name}" vence el {delegacion.fecha_limite}',
                user_id=delegacion.usuario_delegante_id.id
            )
    
    @api.model
    def crear_delegacion_automatica(self, oferta_id, tipo_delegacion, usuario_delegado_id, motivo):
        """Crea una delegación automática"""
        oferta = self.env['oferta.oferta'].browse(oferta_id)
        
        # Calcular fecha límite según el tipo de delegación
        dias_limite = {
            'revision_tecnica': 3,
            'aprobacion_comercial': 2,
            'validacion_precios': 1,
            'revision_legal': 5,
            'aprobacion_gerencial': 2,
            'otro': 3
        }
        
        fecha_limite = fields.Date.today() + timedelta(
            days=dias_limite.get(tipo_delegacion, 3)
        )
        
        delegacion_vals = {
            'oferta_id': oferta_id,
            'tipo_delegacion': tipo_delegacion,
            'usuario_delegado_id': usuario_delegado_id,
            'fecha_limite': fecha_limite,
            'motivo_delegacion': motivo,
            'es_obligatoria': tipo_delegacion in ['aprobacion_gerencial', 'revision_legal'],
            'prioridad': 'alta' if oferta.monto_total > 100000 else 'normal'
        }
        
        return self.create(delegacion_vals)