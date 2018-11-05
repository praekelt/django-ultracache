from django.test import TestCase


class TasksTestCase(TestCase):

    def test_import(self):
        from ultracache import tasks
