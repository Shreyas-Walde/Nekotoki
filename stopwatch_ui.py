import sys
import math
import random # Import random for star positions
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QSlider,
                             QFileDialog, QSizePolicy, QShortcut)
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, QRectF, QEvent
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon, QPainter, QPixmap, QCursor, QPainterPath, QKeySequence

# Import the core logic
from stopwatch_core import StopwatchCore

# --- Constants ---
PLAY_ICON = "▶"
PAUSE_ICON = "⏸" # Using the actual pause symbol
RESET_ICON = "⟲"
ADD_BG_ICON = "+"
CLOSE_ICON = "✕"
# -----------------

# Custom Widget to handle background drawing
class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_pixmap = None
        self.scaled_pixmap = None
        # Define base colors without alpha
        self.base_bg_color = QColor(146, 149, 196)
        self.base_border_color = QColor(235, 226, 155)
        # Alpha value controlled by slider (applies to bg or image)
        self.alpha = 120  # Start with default bg alpha
        self.border_alpha = 100 # Keep border alpha separate/fixed for now
        self.border_radius = 15
        self.setMouseTracking(True)
        self.stars = []
        self.num_stars = 50
        # Initialize star pixmap
        self.star_pixmap = None
        # Note: Initial star generation happens on first resize/show
        self._generate_star_points()

    def get_aspect_ratio(self):
        if self.custom_pixmap and not self.custom_pixmap.isNull() and self.custom_pixmap.height() > 0:
            return self.custom_pixmap.width() / self.custom_pixmap.height()
        return None

    def set_image(self, path):
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.custom_pixmap = pixmap
                # Reset alpha to default for images when a new one is set
                self.alpha = 150
                self._update_scaled_pixmap()
                self.update()
                return True # Indicate success
            else:
                print(f"Warning: Could not load image '{path}'")
                self.custom_pixmap = None # Clear if loading failed
                self.scaled_pixmap = None
                # Revert alpha to default for background
                self.alpha = 120
                self.update()
                return False # Indicate failure
        else:
            # Clear image
            self.custom_pixmap = None
            self.scaled_pixmap = None
            # Revert alpha to default for background
            self.alpha = 120
            self.update()
            return True # Indicate success (clearing is success)

    def set_alpha(self, alpha_value):
        """ Sets the alpha value (0-255) used for bg or image opacity """
        self.alpha = max(0, min(255, alpha_value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect_int = self.rect().adjusted(1, 1, -1, -1)
        rect_f = QRectF(rect_int)

        # --- Draw Pre-rendered Stars First ---
        if self.star_pixmap and not self.star_pixmap.isNull():
            painter.drawPixmap(0, 0, self.star_pixmap)

        # --- Draw Background/Image Over Stars ---
        path = QPainterPath()
        path.addRoundedRect(rect_f, self.border_radius, self.border_radius)

        if self.scaled_pixmap:
            painter.setOpacity(self.alpha / 255.0)
            painter.setClipPath(path)
            target_rect = self.rect()
            pixmap_rect = self.scaled_pixmap.rect()
            pixmap_rect.moveCenter(target_rect.center())
            painter.drawPixmap(pixmap_rect.topLeft(), self.scaled_pixmap)
            painter.setOpacity(1.0)
        else:
            # Draw default background
            effective_alpha = max(1, self.alpha)
            temp_bg_color = QColor(self.base_bg_color)
            temp_bg_color.setAlpha(effective_alpha)
            painter.fillPath(path, temp_bg_color)

            # Draw border
            temp_border_color = QColor(self.base_border_color)
            temp_border_color.setAlpha(self.border_alpha)
            pen = painter.pen() # Get painter's current pen
            pen.setColor(temp_border_color)
            pen.setWidth(2)
            painter.setPen(pen) # Apply the modified pen
            # Set painter's brush to NoBrush before drawing the path outline
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

    def resizeEvent(self, event):
        """ Called automatically when the widget is resized. """
        super().resizeEvent(event)
        # Regenerate stars pixmap on resize
        self._update_star_pixmap()
        # Rescale the background image
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        """ Helper function to rescale the pixmap based on current size. """
        if self.custom_pixmap and not self.custom_pixmap.isNull():
            target_size = self.size()
            if target_size.isValid():
                # Scale pixmap using FastTransformation for potentially lower resource usage
                self.scaled_pixmap = self.custom_pixmap.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
            else:
                self.scaled_pixmap = None # Clear if size is invalid
        else:
            self.scaled_pixmap = None # Clear if no original pixmap

    def _generate_star_points(self):
        """ Generates random star positions within the widget bounds. """
        self.stars = []
        w = self.width()
        h = self.height()
        if w > 0 and h > 0:
            for _ in range(self.num_stars):
                x = random.randint(0, w - 1)
                y = random.randint(0, h - 1)
                self.stars.append(QPoint(x, y))
        # No update() call here

    def _update_star_pixmap(self):
        """ Creates/updates the pixmap with stars drawn onto it. """
        size = self.size()
        if not size.isValid():
            self.star_pixmap = None
            return

        # Generate the positions
        self._generate_star_points()

        # Create pixmap with transparency
        self.star_pixmap = QPixmap(size)
        self.star_pixmap.fill(Qt.transparent)

        # Paint stars onto the pixmap
        star_painter = QPainter(self.star_pixmap)
        # Optional: Disable antialiasing for tiny dots for performance?
        # star_painter.setRenderHint(QPainter.Antialiasing, False)
        star_painter.setPen(Qt.NoPen)
        star_painter.setBrush(QColor(255, 255, 255, 200)) # Semi-transparent white

        for star_pos in self.stars:
            star_painter.drawEllipse(star_pos, 1, 1) # Draw 1x1 pixel dots

        star_painter.end()
        self.update() # Trigger widget repaint now that pixmap is ready

class NekoToki(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instantiate the core logic
        self.core = StopwatchCore(self) # Pass self as parent if needed

        # Window attributes
        self.setWindowTitle("NekoToki")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Size and position
        self.resize(200, 100)
        self.minimum_size = QPoint(150, 80)

        # Aspect Ratio Lock State
        self.aspect_ratio_locked = False
        self.current_aspect_ratio = 200.0 / 100.0 # Default aspect ratio

        # For window dragging and resizing
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.offset = QPoint()
        self.border_margin = 5 # Pixels margin for resize detection

        # UI setup
        self.init_ui()

        # Connect core signals to UI slots
        self.core.time_updated.connect(self._update_time_display)
        self.core.status_changed.connect(self._update_button_state)

        # Setup Keyboard Shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """ Creates application-wide keyboard shortcuts. """
        # Using Qt.Key enums for potentially better cross-layout compatibility
        shortcut_toggle = QShortcut(QKeySequence(Qt.AltModifier | Qt.Key_Plus), self)
        shortcut_pause = QShortcut(QKeySequence(Qt.AltModifier | Qt.Key_Minus), self)
        shortcut_reset = QShortcut(QKeySequence(Qt.AltModifier | Qt.Key_0), self)

        # Set context to ApplicationShortcut to make them work app-wide
        shortcut_toggle.setContext(Qt.ApplicationShortcut)
        shortcut_pause.setContext(Qt.ApplicationShortcut)
        shortcut_reset.setContext(Qt.ApplicationShortcut)

        shortcut_toggle.activated.connect(self._shortcut_toggle)
        shortcut_pause.activated.connect(self._shortcut_pause)
        shortcut_reset.activated.connect(self._shortcut_reset)

    def init_ui(self):
        """ Initializes all UI elements and layouts. """
        # Central Widget Setup
        self.central_widget = BackgroundWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 5, 10, 10)

        # --- Top Bar Layout --- #
        top_controls_layout = self._create_top_bar_layout()
        main_layout.addLayout(top_controls_layout)

        # --- Background Control Layout (Hidden) --- #
        self.slider_container = self._create_background_controls()
        main_layout.addWidget(self.slider_container)

        # --- Time Display Layout --- #
        time_layout = self._create_time_display_layout()
        main_layout.addLayout(time_layout)

        # --- Main Button Layout --- #
        buttons_layout = self._create_main_buttons_layout()
        main_layout.addLayout(buttons_layout)

    # --- Helper methods for UI Initialization --- #

    def _create_top_bar_layout(self):
        """ Creates the layout containing the add/close buttons. """
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Add Background Button
        self.add_bg_button = QPushButton(ADD_BG_ICON)
        self.add_bg_button.setFixedSize(20, 20)
        self.add_bg_button.setToolTip("Toggle controls (Single Click)\nSelect Background Image (Double Click)")
        self.add_bg_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(235, 226, 155, 140);
                border-radius: 10px; color: rgba(146, 149, 196, 220);
                font-weight: bold; font-size: 14px; padding-bottom: 2px;
            }
            QPushButton:hover { background-color: rgba(235, 226, 155, 180); }
            QPushButton:pressed { background-color: rgba(235, 226, 155, 220); }
        """)
        self.add_bg_button.clicked.connect(self.toggle_background_controls)
        self.add_bg_button.installEventFilter(self) # For double-click
        layout.addWidget(self.add_bg_button)
        layout.addStretch(1)

        # Close Button
        self.close_button = QPushButton(CLOSE_ICON)
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setToolTip("Close NekoToki")
        self.close_button.setStyleSheet("""
             QPushButton {
                 background-color: transparent; border-radius: 10px;
                 color: rgba(235, 226, 155, 220); font-weight: bold; font-size: 12px;
             }
             QPushButton:hover { background-color: rgba(146, 149, 196, 150); }
         """)
        layout.addWidget(self.close_button)
        return layout

    def _create_background_controls(self):
        """ Creates the hidden container for background controls (slider, buttons). """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Alpha Label
        self.slider_label = QLabel("Alpha:")
        self.slider_label.setStyleSheet("color: rgba(235, 226, 155, 220); font-size: 10px;")
        layout.addWidget(self.slider_label)

        # Alpha Slider
        self.bg_alpha_slider = QSlider(Qt.Horizontal)
        self.bg_alpha_slider.setRange(0, 255)
        self.bg_alpha_slider.setValue(self.central_widget.alpha) # Set initial value
        self.bg_alpha_slider.setToolTip("Adjust Background Opacity")
        self.bg_alpha_slider.valueChanged.connect(self.update_background_alpha)
        self.bg_alpha_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.bg_alpha_slider)

        # Change Image Button
        self.change_bg_button = QPushButton("Change Image")
        self.change_bg_button.setToolTip("Select a new background image")
        self.change_bg_button.clicked.connect(self.select_background_image)
        self.change_bg_button.setStyleSheet("font-size: 10px; padding: 2px 5px;")
        layout.addWidget(self.change_bg_button)

        # Reset Background Button
        self.reset_bg_button = QPushButton("Reset BG")
        self.reset_bg_button.setToolTip("Reset to default background")
        self.reset_bg_button.clicked.connect(self.reset_to_default_background)
        self.reset_bg_button.setStyleSheet("font-size: 10px; padding: 2px 5px;")
        layout.addWidget(self.reset_bg_button)

        container.setVisible(False) # Initially hidden
        return container

    def _create_time_display_layout(self):
        """ Creates the centered layout for the time labels. """
        layout = QHBoxLayout()

        # Main Time Label
        self.time_label = QLabel("00:00:00")
        font = QFont("Arial", 24, QFont.Bold)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet("color: rgba(235, 226, 155, 220); background-color: transparent;")
        self.time_label.setAlignment(Qt.AlignVCenter)

        # Centiseconds Label
        self.centiseconds_label = QLabel(".00")
        font.setPointSize(14) # Use existing font object, just change size
        self.centiseconds_label.setFont(font)
        self.centiseconds_label.setStyleSheet("color: rgba(235, 226, 155, 220); background-color: transparent;")
        self.centiseconds_label.setAlignment(Qt.AlignVCenter)

        layout.addStretch(1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.centiseconds_label)
        layout.addStretch(1)
        return layout

    def _create_main_buttons_layout(self):
        """ Creates the layout for the Play/Pause and Reset buttons. """
        layout = QHBoxLayout()

        # Play/Pause Button
        self.play_button = QPushButton(PLAY_ICON)
        self.play_button.clicked.connect(self.core.toggle)
        self.play_button.setStyleSheet("""/* Style set in _update_button_state */""") # Placeholder
        self._update_button_state(self.core.is_running) # Set initial style/text
        self.play_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.play_button.setShortcut("") # Disable default Space activation
        layout.addWidget(self.play_button)

        # Reset Button
        self.reset_button = QPushButton(RESET_ICON)
        self.reset_button.clicked.connect(self.core.reset)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(176, 179, 226, 140);
                border-radius: 10px; color: rgba(235, 226, 155, 220);
                font-weight: bold; border: 1px solid rgba(176, 179, 226, 180);
                padding: 5px;
            }
            QPushButton:hover { background-color: rgba(176, 179, 226, 180); }
            QPushButton:pressed { background-color: rgba(176, 179, 226, 220); }
        """)
        self.reset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.reset_button)
        return layout

    # --- UI Update Slots --- 
    def _update_time_display(self, time_str, centiseconds_str):
        self.time_label.setText(time_str)
        self.centiseconds_label.setText(centiseconds_str)

    def _update_button_state(self, is_running):
        """ Slot to update the play/pause button text and style. """
        if is_running:
            self.play_button.setText(PAUSE_ICON) # Use constant
            # Apply 'Paused' state style (e.g., reddish)
            self.play_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(220, 150, 150, 140); /* Example Reddish */
                    border-radius: 10px; color: rgba(146, 149, 196, 220);
                    font-weight: bold; border: 1px solid rgba(220, 150, 150, 180);
                    padding: 5px;
                }
                QPushButton:hover { background-color: rgba(220, 150, 150, 180); }
                QPushButton:pressed { background-color: rgba(220, 150, 150, 220); }
            """)
        else:
            self.play_button.setText(PLAY_ICON) # Use constant
            # Apply 'Play' state style (original yellow/purple)
            self.play_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(235, 226, 155, 140);
                    border-radius: 10px; color: rgba(146, 149, 196, 220);
                    font-weight: bold; border: 1px solid rgba(235, 226, 155, 180);
                    padding: 5px;
                }
                QPushButton:hover { background-color: rgba(235, 226, 155, 180); }
                QPushButton:pressed { background-color: rgba(235, 226, 155, 220); }
            """)

    # --- Background Control Methods --- 
    def toggle_background_controls(self):
        # Toggle visibility of the slider container
        is_visible = self.slider_container.isVisible()
        self.slider_container.setVisible(not is_visible)

        if not is_visible:
            # If becoming visible, update slider value to current alpha
            self.bg_alpha_slider.setValue(self.central_widget.alpha)
        else:
             # If becoming hidden, unlock aspect ratio only if it was locked
             if self.aspect_ratio_locked:
                 self.aspect_ratio_locked = False

    def select_background_image(self):
        start_dir = ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            # set_image returns True on success (load or clear)
            # It also resets alpha appropriately
            if self.central_widget.set_image(file_path):
                 # Update slider to match new alpha (150 for image)
                 self.bg_alpha_slider.setValue(self.central_widget.alpha)
                 aspect_ratio = self.central_widget.get_aspect_ratio()
                 if aspect_ratio:
                     self.current_aspect_ratio = aspect_ratio
                     self.aspect_ratio_locked = True
                 else:
                     self.aspect_ratio_locked = False
            else:
                 print("Failed to apply image.")
                 # Ensure slider reflects the background alpha (120)
                 self.bg_alpha_slider.setValue(self.central_widget.alpha)
                 self.aspect_ratio_locked = False

    def update_background_alpha(self, value):
        # This directly calls the widget's set_alpha
        self.central_widget.set_alpha(value)

    def reset_to_default_background(self):
        # set_image(None) resets pixmap and alpha to 120
        self.central_widget.set_image(None)
        # Update slider to reflect the new alpha (120)
        self.bg_alpha_slider.setValue(self.central_widget.alpha)
        self.slider_container.setVisible(False) # Hide controls
        self.aspect_ratio_locked = False

    # --- Event Filter for Double Click ---
    def eventFilter(self, source, event):
        """ Catch double clicks specifically on the add_bg_button. """
        if source == self.add_bg_button and event.type() == QEvent.MouseButtonDblClick:
            if event.button() == Qt.LeftButton:
                # On double-click, trigger the image selection
                self.select_background_image()
                return True # Event handled

        # Call base class implementation for other events
        return super().eventFilter(source, event)

    # --- Shortcut Handler Slots --- 
    def _shortcut_toggle(self):
        print("Shortcut Alt+Plus activated") # Debug print
        self.core.toggle()

    def _shortcut_pause(self):
        print("Shortcut Alt+Minus activated") # Debug print
        self.core.pause()

    def _shortcut_reset(self):
        print("Shortcut Alt+0 activated") # Debug print
        self.core.reset()

    # --- Window Dragging and Resizing Logic (Remains the same) ---
    def check_resize_edge(self, pos):
        if self.slider_container.isVisible() and self.slider_container.geometry().contains(pos):
             slider_pos = self.slider_container.mapFrom(self, pos)
             widget_at = self.slider_container.childAt(slider_pos)
             if isinstance(widget_at, QSlider):
                  return None

        rect = self.rect()
        margin = self.border_margin

        on_left = abs(pos.x() - rect.left()) < margin
        on_right = abs(pos.x() - rect.right()) < margin
        on_top = abs(pos.y() - rect.top()) < margin
        on_bottom = abs(pos.y() - rect.bottom()) < margin

        if on_top and on_left: return Qt.SizeBDiagCursor
        if on_top and on_right: return Qt.SizeFDiagCursor
        if on_bottom and on_left: return Qt.SizeFDiagCursor
        if on_bottom and on_right: return Qt.SizeBDiagCursor
        if on_left: return Qt.SizeHorCursor
        if on_right: return Qt.SizeHorCursor
        if on_top: return Qt.SizeVerCursor
        if on_bottom: return Qt.SizeVerCursor

        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPos()
            pos_in_widget = event.pos()

            child_at_pos = self.childAt(pos_in_widget)
            is_on_control = False
            widget = child_at_pos
            while widget:
                if isinstance(widget, (QPushButton, QSlider)):
                    is_on_control = True
                    break
                widget = widget.parent()

            if is_on_control:
                 self.dragging = False
                 self.resizing = False
                 return

            resize_cursor_shape = self.check_resize_edge(pos_in_widget)
            if resize_cursor_shape:
                self.resizing = True
                self.resize_edge = resize_cursor_shape
                self.offset = event.pos()
            elif not is_on_control:
                 self.dragging = True
                 self.offset = event.pos()

    def mouseMoveEvent(self, event):
        pos_in_widget = event.pos()

        if self.resizing and event.buttons() & Qt.LeftButton:
            new_global_pos = event.globalPos()
            current_geo = self.geometry()
            new_geo = QRect(current_geo)
            min_w = self.minimum_size.x()
            min_h = self.minimum_size.y()

            if self.aspect_ratio_locked:
                # --- Aspect Ratio Preserving Resize ---
                # Calculate proposed new geometry based on the dragged edge/corner,
                # then adjust the other dimension to match the aspect ratio,
                # ensuring minimum size constraints are met.
                aspect = self.current_aspect_ratio
                start_press_local = self.offset # Local position where mouse press started

                # Determine which edge/corner is being dragged based on stored resize_edge
                # and the starting position (start_press_local)
                is_top_edge = abs(start_press_local.y() - 0) < self.border_margin * 2
                is_left_edge = abs(start_press_local.x() - 0) < self.border_margin * 2

                if self.resize_edge == Qt.SizeVerCursor: # Top or Bottom edge
                    if is_top_edge:
                        # Calculate new height based on mouse dragging top edge up/down
                        new_top = new_global_pos.y()
                        new_height = max(min_h, current_geo.bottom() - new_top)
                        # Calculate corresponding width based on aspect ratio
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        # Recalculate height in case width hit minimum
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        # Set geometry adjusting top and left
                        new_geo.setTop(current_geo.bottom() - new_height)
                        new_geo.setHeight(new_height)
                        new_geo.setLeft(current_geo.right() - new_width)
                        new_geo.setWidth(new_width)
                    else: # Bottom edge
                        # Calculate new height based on mouse dragging bottom edge down/up
                        new_bottom = new_global_pos.y()
                        new_height = max(min_h, new_bottom - current_geo.top())
                        # Calculate corresponding width
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        # Recalculate height
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        # Set geometry keeping top-left fixed
                        new_geo.setHeight(new_height)
                        new_geo.setWidth(new_width)
                elif self.resize_edge == Qt.SizeHorCursor: # Left or Right edge
                    if is_left_edge:
                        # Calculate new width based on dragging left edge
                        new_left = new_global_pos.x()
                        new_width = max(min_w, current_geo.right() - new_left)
                        # Calculate corresponding height
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        # Recalculate width
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        # Set geometry adjusting left and top
                        new_geo.setLeft(current_geo.right() - new_width)
                        new_geo.setWidth(new_width)
                        new_geo.setTop(current_geo.bottom() - new_height)
                        new_geo.setHeight(new_height)
                    else: # Right edge
                        # Calculate new width based on dragging right edge
                        new_right = new_global_pos.x()
                        new_width = max(min_w, new_right - current_geo.left())
                        # Calculate corresponding height
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        # Recalculate width
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        # Set geometry keeping top-left fixed
                        new_geo.setWidth(new_width)
                        new_geo.setHeight(new_height)
                elif self.resize_edge in [Qt.SizeBDiagCursor, Qt.SizeFDiagCursor]: # Corners
                    # For corners, prioritize vertical change, calculate width, then readjust height
                    mouse_pos = new_global_pos
                    if is_top_edge: # TopLeft or TopRight
                        new_top = mouse_pos.y()
                        new_height = max(min_h, current_geo.bottom() - new_top)
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        new_geo.setTop(current_geo.bottom() - new_height)
                        new_geo.setHeight(new_height)
                        new_geo.setWidth(new_width)
                        if is_left_edge: # TopLeft - adjust left edge
                            new_geo.setLeft(current_geo.right() - new_width)
                        # else TopRight - left edge is fixed
                    else: # BottomLeft or BottomRight
                        new_bottom = mouse_pos.y()
                        new_height = max(min_h, new_bottom - current_geo.top())
                        new_width = max(min_w, math.ceil(new_height * aspect))
                        new_height = max(min_h, math.ceil(new_width / aspect))
                        new_geo.setHeight(new_height)
                        new_geo.setWidth(new_width)
                        if is_left_edge: # BottomLeft - adjust left edge
                            new_geo.setLeft(current_geo.right() - new_width)
                        # else BottomRight - top-left is fixed

                self.setGeometry(new_geo)

            else:
                # --- Free Resizing (No aspect ratio lock) ---
                # Calculate new edge position based on mouse movement, respecting minimum dimensions.
                start_press_local = self.offset
                mouse_pos = new_global_pos

                # Vertical edges (Top / Bottom)
                if self.resize_edge == Qt.SizeVerCursor:
                    mouse_y = mouse_pos.y()
                    if abs(start_press_local.y() - 0) < self.border_margin * 2: # Top edge
                         new_top = mouse_y
                         # Prevent resizing smaller than min height by adjusting top edge
                         if current_geo.height() - (new_top - current_geo.top()) >= min_h:
                              new_geo.setTop(new_top)
                         else:
                              new_geo.setTop(current_geo.bottom() - min_h)
                    else: # Bottom edge
                         new_bottom = mouse_y
                         # Prevent resizing smaller than min height by adjusting bottom edge
                         if new_bottom - current_geo.top() >= min_h:
                              new_geo.setBottom(new_bottom)
                         else:
                              new_geo.setBottom(current_geo.top() + min_h)

                # Horizontal edges (Left / Right)
                elif self.resize_edge == Qt.SizeHorCursor:
                    mouse_x = mouse_pos.x()
                    if abs(start_press_local.x() - 0) < self.border_margin * 2: # Left edge
                         new_left = mouse_x
                         # Prevent resizing smaller than min width
                         if current_geo.width() - (new_left - current_geo.left()) >= min_w:
                               new_geo.setLeft(new_left)
                         else:
                               new_geo.setLeft(current_geo.right() - min_w)
                    else: # Right edge
                         new_right = mouse_x
                         # Prevent resizing smaller than min width
                         if new_right - current_geo.left() >= min_w:
                               new_geo.setRight(new_right)
                         else:
                               new_geo.setRight(current_geo.left() + min_w)

                # Diagonal corners (TopLeft / BottomRight)
                elif self.resize_edge == Qt.SizeBDiagCursor:
                     if abs(start_press_local.y() - 0) < self.border_margin * 2 and abs(start_press_local.x() - 0) < self.border_margin * 2 : # TopLeft
                          new_top = mouse_pos.y()
                          new_left = mouse_pos.x()
                          # Adjust top respecting min height
                          if current_geo.height() - (new_top - current_geo.top()) >= min_h: new_geo.setTop(new_top)
                          else: new_geo.setTop(current_geo.bottom() - min_h)
                          # Adjust left respecting min width
                          if current_geo.width() - (new_left - current_geo.left()) >= min_w: new_geo.setLeft(new_left)
                          else: new_geo.setLeft(current_geo.right() - min_w)
                     else: # BottomRight
                          new_bottom = mouse_pos.y()
                          new_right = mouse_pos.x()
                          # Adjust bottom respecting min height
                          if new_bottom - current_geo.top() >= min_h: new_geo.setBottom(new_bottom)
                          else: new_geo.setBottom(current_geo.top() + min_h)
                          # Adjust right respecting min width
                          if new_right - current_geo.left() >= min_w: new_geo.setRight(new_right)
                          else: new_geo.setRight(current_geo.left() + min_w)

                # Diagonal corners (TopRight / BottomLeft)
                elif self.resize_edge == Qt.SizeFDiagCursor:
                     if abs(start_press_local.y() - 0) < self.border_margin * 2 and abs(start_press_local.x() - current_geo.width()) < self.border_margin * 2: # TopRight
                          new_top = mouse_pos.y()
                          new_right = mouse_pos.x()
                          # Adjust top respecting min height
                          if current_geo.height() - (new_top - current_geo.top()) >= min_h: new_geo.setTop(new_top)
                          else: new_geo.setTop(current_geo.bottom() - min_h)
                          # Adjust right respecting min width
                          if new_right - current_geo.left() >= min_w: new_geo.setRight(new_right)
                          else: new_geo.setRight(current_geo.left() + min_w)
                     else: # BottomLeft
                          new_bottom = mouse_pos.y()
                          new_left = mouse_pos.x()
                          # Adjust bottom respecting min height
                          if new_bottom - current_geo.top() >= min_h: new_geo.setBottom(new_bottom)
                          else: new_geo.setBottom(current_geo.top() + min_h)
                          # Adjust left respecting min width
                          if current_geo.right() - new_left >= min_w:
                               new_geo.setLeft(new_left)
                          else:
                               new_geo.setLeft(current_geo.right() - min_w)

                self.setGeometry(new_geo)

        elif self.dragging and event.buttons() & Qt.LeftButton:
            # --- Window Dragging ---
            self.move(event.globalPos() - self.offset)

        else:
            # --- Update Cursor Shape Based on Position ---
            resize_cursor_shape = self.check_resize_edge(pos_in_widget)
            if resize_cursor_shape:
                self.setCursor(QCursor(resize_cursor_shape))
            else:
                # Check if cursor is over a control widget
                child_at_pos = self.childAt(pos_in_widget)
                is_on_control = False
                widget = child_at_pos
                while widget:
                    if isinstance(widget, (QPushButton, QSlider)):
                         is_on_control = True
                         self.setCursor(Qt.ArrowCursor) # Standard arrow over controls
                         break
                    widget = widget.parent()
                # Use default arrow cursor if not on edge or control
                if not is_on_control:
                     self.unsetCursor()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.unsetCursor()

# Note: The `if __name__ == "__main__":` block is removed from here
# and will be placed in test.py 