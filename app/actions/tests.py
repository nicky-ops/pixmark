from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import Action
from .utils import create_action # Will be used later
import datetime # Will be used later
from django.utils import timezone # Will be used later

class ActionModelTests(TestCase):

    def test_action_model_creation_with_target(self):
        """
        Test creating an Action object with a target.
        """
        user = User.objects.create_user(username='testuser', password='password')
        target_object = User.objects.create_user(username='targetuser', password='password') # Using User as a target

        action = Action.objects.create(
            user=user,
            verb='followed',
            target=target_object
        )

        self.assertEqual(action.user, user)
        self.assertEqual(action.verb, 'followed')
        self.assertEqual(action.target, target_object)
        self.assertIsNotNone(action.created)

        # Check GenericForeignKey fields
        self.assertEqual(action.target_ct, ContentType.objects.get_for_model(target_object))
        self.assertEqual(action.target_id, target_object.id)

    def test_action_model_creation_without_target(self):
        """
        Test creating an Action object without a target.
        """
        user = User.objects.create_user(username='testuser2', password='password')

        action = Action.objects.create(
            user=user,
            verb='logged in'
        )

        self.assertEqual(action.user, user)
        self.assertEqual(action.verb, 'logged in')
        self.assertIsNone(action.target)
        self.assertIsNone(action.target_ct)
        self.assertIsNone(action.target_id)
        self.assertIsNotNone(action.created)


class CreateActionUtilTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='actionuser', password='password')
        self.target_object = User.objects.create_user(username='actiontarget', password='password')

    def test_create_action_without_target(self):
        """
        Test create_action utility function without a target.
        """
        self.assertTrue(create_action(self.user, 'bookmarked image'))
        action = Action.objects.first()
        self.assertEqual(Action.objects.count(), 1)
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.verb, 'bookmarked image')
        self.assertIsNone(action.target)

    def test_create_action_with_target(self):
        """
        Test create_action utility function with a target.
        """
        self.assertTrue(create_action(self.user, 'liked', self.target_object))
        action = Action.objects.first()
        self.assertEqual(Action.objects.count(), 1)
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.verb, 'liked')
        self.assertEqual(action.target, self.target_object)

    def test_create_action_duplicate_within_minute_no_target(self):
        """
        Test that duplicate actions (no target) within a minute are not created.
        """
        self.assertTrue(create_action(self.user, 'logged in')) # First action
        self.assertEqual(Action.objects.count(), 1)

        # Try to create the same action immediately
        self.assertFalse(create_action(self.user, 'logged in'))
        self.assertEqual(Action.objects.count(), 1) # Should still be 1

    def test_create_action_duplicate_within_minute_with_target(self):
        """
        Test that duplicate actions (with target) within a minute are not created.
        """
        self.assertTrue(create_action(self.user, 'viewed', self.target_object)) # First action
        self.assertEqual(Action.objects.count(), 1)

        # Try to create the same action immediately
        self.assertFalse(create_action(self.user, 'viewed', self.target_object))
        self.assertEqual(Action.objects.count(), 1) # Should still be 1

    def test_create_action_same_action_after_one_minute(self):
        """
        Test that the same action can be created if more than a minute has passed.
        """
        # First action
        self.assertTrue(create_action(self.user, 'updated profile'))
        self.assertEqual(Action.objects.count(), 1)
        first_action = Action.objects.first()

        # Manually set the 'created' time of the first action to be more than a minute ago
        first_action.created = timezone.now() - datetime.timedelta(seconds=61)
        first_action.save()

        # Try to create the same action again
        self.assertTrue(create_action(self.user, 'updated profile'))
        self.assertEqual(Action.objects.count(), 2) # Should now be 2
