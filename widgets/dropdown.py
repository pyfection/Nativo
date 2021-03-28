
from kivymd.uix.menu import MDDropdownMenu, MDMenuItemIcon, MDMenuItemRight, MDMenuItem, RightContent, dp


class DropDown(MDDropdownMenu):
    def create_menu_items(self):
        """Creates menu items."""

        for data in self.items:
            if data.get("icon") and data.get("right_content_cls", None):

                item = MDMenuItemIcon(
                    text=data.get("text", ""),
                    divider=data.get("divider", "Full"),
                    _txt_top_pad=data.get("top_pad", "20dp"),
                    _txt_bot_pad=data.get("bot_pad", "20dp"),
                )

            elif data.get("icon"):
                item = MDMenuItemIcon(
                    text=data.get("text", ""),
                    divider=data.get("divider", "Full"),
                    _txt_top_pad=data.get("top_pad", "20dp"),
                    _txt_bot_pad=data.get("bot_pad", "20dp"),
                )

            elif data.get("right_content_cls", None):
                item = MDMenuItemRight(
                    text=data.get("text", ""),
                    divider=data.get("divider", "Full"),
                    _txt_top_pad=data.get("top_pad", "20dp"),
                    _txt_bot_pad=data.get("bot_pad", "20dp"),
                )

            else:

                item = MDMenuItem(
                    text=data.get("text", ""),
                    divider=data.get("divider", "Full"),
                    _txt_top_pad=data.get("top_pad", "20dp"),
                    _txt_bot_pad=data.get("bot_pad", "20dp"),
                )
            item.data = data

            # Set height item.
            if data.get("height", ""):
                item.height = data.get("height")
            # Compensate icon area by some left padding.
            if not data.get("icon"):
                item._txt_left_pad = data.get("left_pad", "32dp")
            # Set left icon.
            else:
                item.icon = data.get("icon", "")
            item.bind(on_release=lambda x=item: self.dispatch("on_release", x))
            right_content_cls = data.get("right_content_cls", None)
            # Set right content.
            if isinstance(right_content_cls, RightContent):
                item.ids._right_container.width = right_content_cls.width + dp(
                    20
                )
                item.ids._right_container.padding = ("10dp", 0, 0, 0)
                item.add_widget(right_content_cls)
            else:
                if "_right_container" in item.ids:
                    item.ids._right_container.width = 0
            self.menu.ids.box.add_widget(item)
