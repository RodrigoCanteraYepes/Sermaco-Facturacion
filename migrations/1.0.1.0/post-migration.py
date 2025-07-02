# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración para actualizar el campo es_valida en oferta.clausula
    después de agregar store=True
    """
    # Forzar el recálculo del campo es_valida para todos los registros existentes
    cr.execute("""
        UPDATE oferta_clausula 
        SET es_valida = CASE 
            WHEN (fecha_inicio IS NULL OR fecha_inicio <= CURRENT_DATE) 
                 AND (fecha_fin IS NULL OR fecha_fin >= CURRENT_DATE) 
            THEN TRUE 
            ELSE FALSE 
        END
    """)