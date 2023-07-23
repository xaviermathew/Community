class CommunityRouter:
    @staticmethod
    def is_django_managed_model(model):
        table = model._meta.db_table
        return '_' in table and not table.startswith('rainman_')

    @staticmethod
    def is_rainman_model(model):
        table = model._meta.db_table
        return table.startswith('rainman_')

    def db_for_read(self, model, **hints):
        if self.is_django_managed_model(model):
            return None
        elif self.is_rainman_model(model):
            return 'rainman'
        else:
            return 'community'

    def db_for_write(self, model, **hints):
        if self.is_django_managed_model(model):
            return None
        elif self.is_rainman_model(model):
            return 'rainman'
        else:
            return 'community'

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'community':
            return False
        elif db == 'rainman':
            return False
        else:
            return None
