
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang.builder import Builder


Builder.load_file('pages/auth.kv')


class AuthPage(Screen):
    def submit(self, method, email, password):
        print('try', method, 'with', email, password)

        if method == 'register':
            try:
                App.get_running_app().db.create_user(email, password)
            except KeyError:
                print('User already exists!')  # ToDo: replace with popup

        elif method == 'login':
            verified = App.get_running_app().db.verify_user(email, password)
            if verified:
                self.root.goto('main')
                App.get_running_app().authenticated = True
            else:
                print("Could not log in user, try again")  # ToDo: replace with popup

        else:
            raise KeyError("Submit method can only be 'register' or 'login'")

    def skip(self):
        # Skips registration, but user can't create objects
        self.root.goto('main')
