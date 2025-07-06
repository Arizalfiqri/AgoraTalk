# forum/database_router.py

class DatabaseRouter:
    """
    Router untuk memisahkan database admin dan user biasa
    """
    
    def db_for_read(self, model, **hints):
        """Menentukan database untuk operasi read"""
        if model._meta.app_label == 'forum':
            if model.__name__ == 'AdminUser':
                return 'admin_db'
            else:
                return 'default'
        return None
    
    def db_for_write(self, model, **hints):
        """Menentukan database untuk operasi write"""
        if model._meta.app_label == 'forum':
            if model.__name__ == 'AdminUser':
                return 'admin_db'
            else:
                return 'default'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Mengizinkan relasi antar objek dalam database yang sama"""
        if obj1._meta.app_label == 'forum' and obj2._meta.app_label == 'forum':
            # Jangan izinkan relasi antara AdminUser dan model lain
            if (obj1.__class__.__name__ == 'AdminUser' and obj2.__class__.__name__ != 'AdminUser') or \
                (obj2.__class__.__name__ == 'AdminUser' and obj1.__class__.__name__ != 'AdminUser'):
                return False
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Mengontrol migrasi model ke database yang tepat"""
        if app_label == 'forum':
            if model_name == 'adminuser':
                return db == 'admin_db'
            else:
                return db == 'default'
        elif app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
            # Model Django default bisa di kedua database
            return True
        return None
    
