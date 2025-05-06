def migrate(cr, version):
    """
    This migration script fixes service extension relationships
    after upgrading the module.
    
    Args:
        cr: Database cursor
        version: Previous module version
    """
    if not version:
        return
    
    # Log the start of the migration
    cr.execute("INSERT INTO ir_logging(name, type, dbname, level, message, path, line, func) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
               ('clau_hosting_domain', 'server', cr.dbname, 'info', 'Starting service extension migration', 'post-migrate.py', 1, 'migrate'))
    
    # Check if service_type column exists, create it if not
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='service_extension' AND column_name='service_type'
    """)
    if not cr.fetchone():
        # Column doesn't exist, so create it
        cr.execute("""
            ALTER TABLE service_extension 
            ADD COLUMN service_type VARCHAR
        """)
        
    # Now update service_type for existing records
    cr.execute("""
        UPDATE service_extension 
        SET service_type = SPLIT_PART(service_id, ',', 1)
        WHERE service_id IS NOT NULL
    """)
    
    # Log completion
    cr.execute("INSERT INTO ir_logging(name, type, dbname, level, message, path, line, func) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
               ('clau_hosting_domain', 'server', cr.dbname, 'info', 'Service extension migration completed', 'post-migrate.py', 1, 'migrate'))