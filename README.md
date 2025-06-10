# Bookmarks
Bookmarks is a dynamic web application built in django that allows authenticated users to bookmark images from other websites using a javascript bookmarklet. It also allows authenticated users to like other users' images and follow each other.

### Features

- User authentication: Users can create an account, log in, and log out.
- Bookmark creation: Users can add new bookmarks by adding the bookmark it button to their bookmarks bar on their browser.
- Bookmark management: Users can view and like bookmarked images.
- Follow system: Users can follow each other and have an activity stream of the creators they follow.
- Image ranking: images are ranked according to the number of likes
### Installation

To run this project locally, follow these steps:

1. Clone the repository: `git clone https://github.com/nicky-ops/django_practice.git`
2. Navigate to the project directory: `cd bookmarks`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Set up the database: `python manage.py migrate`
5. Start the development server: `python manage.py runserver`

### Usage

Once the development server is running, you can access the application by visiting `http://localhost:8000` in your web browser. From there, you can create an account, log in, and start managing your bookmarks.

### Contributing

If you'd like to contribute to this project, please follow these guidelines:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request.

### License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more information.
## 

