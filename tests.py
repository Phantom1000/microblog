from datetime import datetime, timezone, timedelta
import unittest
from app import create_app, db
from app.models.user import User
from app.models.post import Post
from config import TestConfig


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        user = User(username='Иван', email='ivan@example.com')
        user.set_password('123')
        self.assertFalse(user.check_password('000'))
        self.assertTrue(user.check_password('123'))

    def test_avatar(self):
        user = User(username='Петр', email='petr@example.com')
        self.assertEqual(user.avatar(128), ('https://www.gravatar.com/avatar/'
                                            '565c7ae7912e8be4f8c4df872c76606c'
                                            '?d=identicon&s=128'))

    def test_follow(self):
        user1 = User(username='Иван', email='ivan@example.com')
        user2 = User(username='Петр', email='petr@example.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        following = db.session.scalars(user1.following.select()).all()
        followers = db.session.scalars(user2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        user1.follow(user2)
        db.session.commit()
        self.assertTrue(user1.is_following(user2))
        self.assertEqual(user1.following_count(), 1)
        self.assertEqual(user2.followers_count(), 1)
        user1_following = db.session.scalars(user1.following.select()).all()
        user2_followers = db.session.scalars(user2.followers.select()).all()
        self.assertEqual(user1_following[0].username, 'Петр')
        self.assertEqual(user2_followers[0].username, 'Иван')

        user1.unfollow(user2)
        db.session.commit()
        self.assertFalse(user1.is_following(user2))
        self.assertEqual(user1.following_count(), 0)
        self.assertEqual(user2.followers_count(), 0)

    def test_follow_posts(self):
        user1 = User(username='Иван', email='ivan@example.com')
        user2 = User(username='Петр', email='petr@example.com')
        user3 = User(username='Мария', email='maria@example.com')
        user4 = User(username='Александр', email='alexandr@example.com')
        db.session.add_all([user1, user2, user3, user4])

        now = datetime.now(timezone.utc)
        post1 = Post(body="Пост Ивана", author=user1, timestamp=now + timedelta(seconds=1))
        post2 = Post(body="Пост Петра", author=user2, timestamp=now + timedelta(seconds=4))
        post3 = Post(body="Пост Марии", author=user3, timestamp=now + timedelta(seconds=3))
        post4 = Post(body="Пост Александра", author=user4, timestamp=now + timedelta(seconds=2))
        db.session.add_all([post1, post2, post3, post4])
        db.session.commit()

        user1.follow(user2)
        user1.follow(user4)
        user2.follow(user3)
        user3.follow(user4)
        db.session.commit()

        user1_following_posts = db.session.scalars(user1.following_posts()).all()
        user2_following_posts = db.session.scalars(user2.following_posts()).all()
        user3_following_posts = db.session.scalars(user3.following_posts()).all()
        user4_following_posts = db.session.scalars(user4.following_posts()).all()
        self.assertEqual(user1_following_posts, [post2, post4, post1])
        self.assertEqual(user2_following_posts, [post2, post3])
        self.assertEqual(user3_following_posts, [post3, post4])
        self.assertEqual(user4_following_posts, [post4])


if __name__ == '__main__':
    unittest.main(verbosity=2)
