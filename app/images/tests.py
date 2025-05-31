from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType # Added this import
from django.utils.text import slugify
from django.urls import reverse
from .models import Image
# For mocking requests.get in form tests later
# from unittest.mock import patch, MagicMock
# For testing file fields
# from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import MagicMock

class ImageModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_image_model_creation_and_fields(self):
        """
        Test creating an Image object and that its fields are correctly set.
        """
        image = Image.objects.create(
            user=self.user,
            title='Test Image Title',
            url='http://example.com/testimage.jpg',
            # image field would typically be created by form save or manually for test
            description='A description for the test image.'
        )
        # Simulate file being saved, as model itself doesn't populate image field
        # In a real scenario, this would be an actual image file
        image.image.name = 'images/testimage.jpg'
        image.save() # To trigger slug generation if not already done by create

        self.assertEqual(image.user, self.user)
        self.assertEqual(image.title, 'Test Image Title')
        self.assertEqual(image.slug, slugify(image.title)) # Check slug generation
        self.assertEqual(image.url, 'http://example.com/testimage.jpg')
        self.assertEqual(image.image.name, 'images/testimage.jpg')
        self.assertEqual(image.description, 'A description for the test image.')
        self.assertIsNotNone(image.created)
        self.assertEqual(image.users_like.count(), 0)
        self.assertEqual(image.total_likes, 0)

    def test_image_save_method_slug_generation(self):
        """
        Test that the save method correctly generates a slug if it's not provided.
        """
        image = Image(
            user=self.user,
            title='Another Test Image',
            url='http://example.com/another.png'
        )
        image.image.name = 'images/another.png'
        image.save() # Slug should be generated here
        self.assertEqual(image.slug, 'another-test-image')

        # Test that an existing slug is not overwritten
        image2 = Image(
            user=self.user,
            title='Yet Another Image',
            slug='custom-slug-test',
            url='http://example.com/yet.gif'
        )
        image2.image.name = 'images/yet.gif'
        image2.save()
        self.assertEqual(image2.slug, 'custom-slug-test')

    def test_image_get_absolute_url(self):
        """
        Test the get_absolute_url method.
        """
        image = Image.objects.create(
            user=self.user,
            title='URL Test Image',
            url='http://example.com/urltest.jpg'
        )
        image.image.name = 'images/urltest.jpg'
        # Slug is generated on save, so save it if not using create which calls save
        # Image.objects.create already calls save, so slug is set.

        expected_url = reverse('images:detail', args=[image.id, image.slug])
        self.assertEqual(image.get_absolute_url(), expected_url)

    def test_image_str_representation(self):
        """
        Test the string representation of the Image model.
        """
        image = Image.objects.create(
            user=self.user,
            title='String Test',
            url='http://example.com/string.jpg'
        )
        self.assertEqual(str(image), 'String Test')


from django.core.files.base import ContentFile
from unittest.mock import patch, MagicMock
from actions.models import Action
from django.test import override_settings

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
@patch('images.views.r', MagicMock()) # Patch redis client 'r' in views globally for this test class
class ImageCreateViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser_create', password='password')
        self.client.login(username='testuser_create', password='password')
        # URL for the image_create view
        self.create_url = reverse('images:create')

        # Configure the mock for 'r' if needed for specific return values per test
        # For image_detail, r.incr returns the new value, r.zincrby also returns new score.
        self.mock_redis = MagicMock()
        self.mock_redis.incr.return_value = 1
        self.mock_redis.zincrby.return_value = 1
        images_views_r_patcher = patch('images.views.r', self.mock_redis)
        self.addCleanup(images_views_r_patcher.stop) # Stop patch after test methods in class
        images_views_r_patcher.start()


    @patch('images.forms.requests.get') # Mock requests.get used in ImageCreateForm
    def test_image_create_view_valid_post(self, mock_requests_get):
        """
        Test the image_create view with a valid POST request.
        """
        # Configure the mock for requests.get
        mock_response = mock_requests_get.return_value
        mock_response.status_code = 200
        mock_response.content = b"R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" # Minimal valid GIF

        image_title = 'New Test Image'
        image_url = 'http://example.com/new_image.jpg'
        image_description = 'Description for new image.'

        post_data = {
            'title': image_title,
            'url': image_url, # This is normally hidden and filled by JS bookmarklet
            'description': image_description,
        }

        response = self.client.post(self.create_url, post_data)

        # Check if an Image object was created
        self.assertTrue(Image.objects.filter(user=self.user, title=image_title).exists())
        new_image = Image.objects.get(user=self.user, title=image_title)

        # Check redirection to the image's detail page
        self.assertRedirects(response, new_image.get_absolute_url())

        # Check if an Action was created
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(new_image)
        self.assertTrue(
            Action.objects.filter(
                user=self.user,
                verb='bookmarked image',
                target_ct=content_type,
                target_id=new_image.id
            ).exists()
        )

        # Verify that requests.get was called with the correct URL
        mock_requests_get.assert_called_once_with(image_url)

        # Check that the image file was "saved" (mocked save)
        self.assertTrue(new_image.image.name.endswith('.jpg'))


# Test image liking functionality (ImageLikeViewTests class) will go here
class ImageLikeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='likeuser', password='password')
        self.client.login(username='likeuser', password='password')
        self.image = Image.objects.create(
            user=self.user, # Or another user, depending on test case
            title='Image to Like',
            url='http://example.com/like_image.jpg',
            description='Test image for liking.'
        )
        self.image.image.name = 'images/like_image.jpg' # Simulate image file
        self.image.save()
        self.like_url = reverse('images:like')

        # Mock redis for action creation if it's too fast
        self.mock_redis_actions = MagicMock()
        # Prevent create_action from blocking due to time limits
        self.mock_redis_actions.filter.return_value.exists.return_value = False
        # If create_action uses Action.objects.filter directly
        # then patch 'actions.utils.Action.objects.filter'

        # For the create_action utility function, we might need to ensure
        # that the duplicate check doesn't interfere if actions are created rapidly.
        # A simple way is to ensure verbs are different or patch the check.
        # For now, we assume 'likes' action can be created.
        # If actions.utils.similar_actions.exists() is problematic, patch it.
        # We will also patch the main redis 'r' for views consistency
        self.mock_redis_view = MagicMock()
        images_views_r_patcher = patch('images.views.r', self.mock_redis_view)
        self.addCleanup(images_views_r_patcher.stop)
        images_views_r_patcher.start()


    def test_image_like_and_unlike(self):
        """
        Test liking and unliking an image via the image_like view.
        """
        # 1. Like the image
        response_like = self.client.post(
            self.like_url,
            {'id': self.image.id, 'action': 'like'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response_like.status_code, 200)
        self.assertEqual(response_like.json()['status'], 'ok')
        self.image.refresh_from_db() # Reload from DB to see changes
        self.assertIn(self.user, self.image.users_like.all())

        # Check if "like" action was created
        content_type = ContentType.objects.get_for_model(self.image)
        self.assertTrue(
            Action.objects.filter(
                user=self.user,
                verb='likes',
                target_ct=content_type,
                target_id=self.image.id
            ).exists()
        )
        initial_action_count = Action.objects.count()

        # 2. Unlike the image
        response_unlike = self.client.post(
            self.like_url,
            {'id': self.image.id, 'action': 'unlike'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response_unlike.status_code, 200)
        self.assertEqual(response_unlike.json()['status'], 'ok')
        self.image.refresh_from_db() # Reload
        self.assertNotIn(self.user, self.image.users_like.all())

        # Verify no new action was created for "unlike" as per current view logic
        self.assertEqual(Action.objects.count(), initial_action_count)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ImageDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='detailuser', password='password')
        self.image = Image.objects.create(
            user=self.user,
            title='Detail Test Image',
            slug='detail-test-image', # Slug must be set for get_absolute_url
            url='http://example.com/detail_image.jpg',
        )
        self.image.image.name = 'images/detail_image.jpg' # Simulate image file
        self.image.save() # Ensure slug is definitely saved

        self.detail_url = self.image.get_absolute_url()

        # Mock Redis
        self.mock_redis = MagicMock()
        self.mock_redis.incr.return_value = 1  # Simulate view increment
        self.mock_redis.zincrby.return_value = 1 # Simulate ranking increment

        # Patch 'images.views.r' for all methods in this class
        images_views_r_patcher = patch('images.views.r', self.mock_redis)
        self.addCleanup(images_views_r_patcher.stop)
        images_views_r_patcher.start()

    def test_image_detail_view_get_request(self):
        """
        Test a GET request to the image_detail view.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.title)
        self.assertTemplateUsed(response, 'images/image/detail.html')

        # Check if Redis incr and zincrby were called
        self.mock_redis.incr.assert_called_once_with(f'image:{self.image.id}:views')
        self.mock_redis.zincrby.assert_called_once_with('image_ranking', 1, self.image.id)

        # Check if total_views is in context (optional, depends on strictness)
        # self.assertEqual(response.context['total_views'], 1)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ImageListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='listuser', password='password')
        self.client.login(username='listuser', password='password') # Added login
        # Create a few images to test pagination and listing
        self.image1 = Image.objects.create(user=self.user, title='List Image 1', url='http://example.com/list1.jpg')
        self.image1.image.name = 'images/list1.jpg'; self.image1.save()
        self.image2 = Image.objects.create(user=self.user, title='List Image 2', url='http://example.com/list2.jpg')
        self.image2.image.name = 'images/list2.jpg'; self.image2.save()
        self.list_url = reverse('images:list')

    def test_image_list_view_get_request(self):
        """
        Test a GET request to the image_list view.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/list.html')
        self.assertContains(response, self.image1.title)
        self.assertContains(response, self.image2.title)
        # Check context for images (optional, depends on how many are on first page by default)
        # self.assertIn('images', response.context)
        # if response.context['images']:
        #     self.assertEqual(len(response.context['images']), 2) # Assuming default pagination shows these


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ImageRankingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='rankuser', password='password')
        self.client.login(username='rankuser', password='password')

        # Create some images that will be "ranked"
        self.image1 = Image.objects.create(user=self.user, title='Rank Image 1', url='http://example.com/rank1.jpg')
        self.image1.image.name = 'images/rank1.jpg'; self.image1.save()
        self.image2 = Image.objects.create(user=self.user, title='Rank Image 2', url='http://example.com/rank2.jpg')
        self.image2.image.name = 'images/rank2.jpg'; self.image2.save()

        self.ranking_url = reverse('images:ranking')

        # Mock Redis
        self.mock_redis = MagicMock()
        # Simulate zrange returning IDs of our created images, as bytes (important)
        # The view code converts them to int: image_ranking_ids = [int(id) for id in image_ranking]
        self.mock_redis.zrange.return_value = [str(self.image1.id).encode(), str(self.image2.id).encode()]

        images_views_r_patcher = patch('images.views.r', self.mock_redis)
        self.addCleanup(images_views_r_patcher.stop)
        images_views_r_patcher.start()

    def test_image_ranking_view_get_request(self):
        """
        Test a GET request to the image_ranking view.
        """
        response = self.client.get(self.ranking_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'images/image/ranking.html')

        # Check that the mock was called correctly
        self.mock_redis.zrange.assert_called_once_with('image_ranking', 0, -1, desc=True)

        # Check if the ranked images are in the context and in the correct order
        # The view sorts 'most_viewed' based on the order from Redis
        self.assertIn('most_viewed', response.context)
        most_viewed_in_context = response.context['most_viewed']
        self.assertEqual(len(most_viewed_in_context), 2)
        if len(most_viewed_in_context) == 2: # Avoid index error if previous assert fails
            self.assertEqual(most_viewed_in_context[0].id, self.image1.id)
            self.assertEqual(most_viewed_in_context[1].id, self.image2.id)
            self.assertContains(response, self.image1.title)
            self.assertContains(response, self.image2.title)
