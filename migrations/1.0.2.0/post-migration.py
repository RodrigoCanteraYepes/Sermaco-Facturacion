# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migración para actualizar el campo es_valida en oferta.clausula
    después de agregar store=True
    """
    # Verificar si la columna es_valida existe, si no, crearla
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='oferta_clausula' AND column_name='es_valida'
    """)
    
    if not cr.fetchone():
        # Crear la columna si no existe
        cr.execute("ALTER TABLE oferta_clausula ADD COLUMN es_valida boolean")
    
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
    
    # Crear índice para mejorar el rendimiento de las búsquedas
    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_oferta_clausula_es_valida 
        ON oferta_clausula(es_valida)
    """)