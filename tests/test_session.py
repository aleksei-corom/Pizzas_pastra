import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session import Session
from database.models import Usuario

class TestSession(unittest.TestCase):
    def setUp(self):
        # Reset the singleton state
        Session._instance = None
        self.session = Session.get()

    def tearDown(self):
        Session._instance = None

    def test_singleton(self):
        s1 = Session.get()
        s2 = Session.get()
        self.assertIs(s1, s2)

    def test_login_logout(self):
        self.assertFalse(self.session.is_logged_in)
        self.assertIsNone(self.session.user)
        
        user = Usuario(id=1, username="test", rol="cajero")
        self.session.login(user)
        
        self.assertTrue(self.session.is_logged_in)
        self.assertEqual(self.session.user.username, "test")
        
        self.session.logout()
        self.assertFalse(self.session.is_logged_in)

    def test_role_access(self):
        # Test admin
        admin_user = Usuario(id=1, username="admin1", rol="admin")
        self.session.login(admin_user)
        
        self.assertTrue(self.session.is_admin())
        self.assertTrue(self.session.has_access("dashboard"))
        self.assertTrue(self.session.has_access("contabilidad"))
        self.assertTrue(self.session.has_access("pos"))
        
        # Test cajero
        self.session.logout()
        cajero_user = Usuario(id=2, username="cajero1", rol="cajero")
        self.session.login(cajero_user)
        
        self.assertFalse(self.session.is_admin())
        self.assertTrue(self.session.has_access("pos"))
        self.assertTrue(self.session.has_access("ordenes"))
        self.assertFalse(self.session.has_access("dashboard"))
        self.assertFalse(self.session.has_access("contabilidad"))

if __name__ == '__main__':
    unittest.main()
