from django.db.backends.mysql import base
from django.db.backends.mysql import features
from django.utils.functional import cached_property


class DatabaseFeatures(features.DatabaseFeatures):
    @cached_property
    def is_sql_auto_is_null_enabled(self):
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT @@SQL_AUTO_IS_NULL')
            result = cursor.fetchone()
            return result and result['@@SQL_AUTO_IS_NULL'] == 1


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures

    def create_cursor(self, name=None):
        cursor = self.connection.cursor(self.Database.cursors.DictCursor)
        return base.CursorWrapper(cursor)

    @cached_property
    def mysql_server_info(self):
        with self.temporary_connection() as cursor:
            cursor.execute('SELECT VERSION()')
            return cursor.fetchone()['VERSION()']