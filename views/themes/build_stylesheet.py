
def build_stylesheet(theme: dict) -> str:
    base = """
    /* === BASE === */
    QWidget {
        background-color: {{bg}};
        color: {{fg}};
        font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Noto Sans', sans-serif;
        font-size: 13px;
    }
    /* === BOTONES === */
    QPushButton {
        background-color: {{primary}};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
        min-height: 18px;
    }
    QPushButton:hover { background-color: {{primary_hover}}; }
    QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
    QPushButton:disabled { background-color: {{bg_input}}; color: {{fg_muted}}; }

    QPushButton[class="secondary"] {
        background-color: transparent;
        color: {{primary}};
        border: 1.5px solid {{primary}};
    }
    QPushButton[class="secondary"]:hover { background-color: {{primary_light}}; }

    QPushButton[class="ghost"] {
        background-color: transparent;
        color: {{fg_muted}};
        border: none;
    }
    QPushButton[class="ghost"]:hover { background-color: {{primary_light}}; color: {{primary}}; }

    QPushButton[class="danger"] { background-color: {{danger}}; }
    QPushButton[class="danger"]:hover { background-color: {{danger_hover}}; }

    QPushButton[class="danger-ghost"] {
        background-color: transparent;
        color: {{danger}};
        border: none;
        padding: 0px; min-height: 0px;
    }
    QPushButton[class="danger-ghost"]:hover { background-color: rgba(239,68,68,0.1); }

    /* === ICON BUTTONS === */
    QPushButton[class="icon-action"] {
        background: transparent; border: none; font-size: 14px; border-radius: 6px; padding: 0px; min-height: 0px;
    }
    QPushButton[class="icon-action"]:hover { background: {{bg_input}}; }

    QPushButton[class="icon-warning"] {
        background: transparent; border: none; font-size: 16px; border-radius: 8px; padding: 0px; min-height: 0px; color: {{warning}};
    }
    QPushButton[class="icon-warning"]:hover { background: rgba(251,191,36,0.15); }

    QPushButton[class="icon-danger"] {
        background: transparent; border: none; font-size: 16px; border-radius: 8px; padding: 0px; min-height: 0px; color: {{danger}};
    }
    QPushButton[class="icon-danger"]:hover { background: rgba(248,113,113,0.15); }

    QPushButton[class="icon-success"] {
        background: transparent; border: none; font-size: 16px; border-radius: 8px; padding: 0px; min-height: 0px; color: {{success}};
    }
    QPushButton[class="icon-success"]:hover { background: rgba(52,211,153,0.15); }

    QPushButton[class="icon-btn"] {
        background-color: transparent; border: none;
        border-radius: 8px; font-size: 16px; color: {{fg_muted}};
        padding: 0px; min-height: 0px;
    }
    QPushButton[class="icon-btn"]:hover {
        background-color: rgba(255,255,255,0.08); color: {{fg}};
    }


    /* === INPUTS === */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
        background-color: {{bg_input}};
        color: {{fg}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        selection-background-color: {{primary}};
        selection-color: #ffffff;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
        border-color: {{primary}};
    }
    QLineEdit::placeholder, QTextEdit::placeholder { color: {{fg_muted}}; }

    /* === COMBOBOX === */
    QComboBox {
        background-color: {{bg_input}};
        color: {{fg}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 36px;
        min-height: 18px;
    }
    QComboBox:focus { border-color: {{primary}}; }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: right center;
        width: 32px;
        border: none;
        background: transparent;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {{fg_muted}};
    }
    QComboBox QAbstractItemView {
        background-color: {{bg_card}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 8px;
        selection-background-color: {{primary_light}};
        selection-color: {{primary}};
        padding: 4px;
        outline: none;
    }

    /* === CALENDAR WIDGET === */
    QCalendarWidget QWidget { alternate-background-color: {{bg_card}}; }
    QCalendarWidget QTableView::item {
        padding: 0px;
        border: none;
    }
    QCalendarWidget QHeaderView::section {
        padding: 2px;
        font-size: 11px;
        border: none;
        background-color: {{bg_card}};
    }
    QCalendarWidget QAbstractItemView:enabled {
        color: {{fg}};
        background-color: {{bg_card}};
        selection-background-color: {{primary}};
        selection-color: #ffffff;
    }
    QCalendarWidget QAbstractItemView:disabled { color: {{fg_muted}}; }
    QCalendarWidget QToolButton {
        color: {{fg}};
        background-color: transparent;
        border: none;
        border-radius: 4px;
        font-weight: 600;
    }
    QCalendarWidget QToolButton:hover { background-color: {{bg_input}}; }
    QCalendarWidget QMenu { background-color: {{bg_card}}; color: {{fg}}; }
    QCalendarWidget QSpinBox { background-color: {{bg_input}}; color: {{fg}}; }

    /* === TABLA === */
    QTableWidget, QTableView {
        background-color: {{bg_card}};
        alternate-background-color: {{bg_input}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 12px;
        gridline-color: {{border}};
        font-size: 13px;
    }
    QTableWidget::item, QTableView::item {
        padding: 10px 14px;
        border-bottom: 1px solid {{border}};
    }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: {{primary_light}};
        color: {{primary}};
    }
    QHeaderView::section {
        background-color: {{bg_input}};
        color: {{fg_muted}};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 14px;
        border: none;
        border-bottom: 2px solid {{border}};
    }
    QHeaderView::section:first { border-top-left-radius: 12px; }
    QHeaderView::section:last { border-top-right-radius: 12px; }

    /* === LISTWIDGET / TREEWIDGET === */
    QListWidget, QTreeWidget {
        background-color: {{bg_card}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 12px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item, QTreeWidget::item {
        padding: 10px 14px;
        border-radius: 8px;
    }
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: {{primary_light}};
        color: {{primary}};
    }
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: {{bg_input}};
    }

    /* === SCROLLBAR === */
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: {{border}};
        border-radius: 4px;
        min-height: 40px;
    }
    QScrollBar::handle:vertical:hover { background: {{fg_muted}}; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: {{border}};
        border-radius: 4px;
        min-width: 40px;
    }
    QScrollBar::handle:horizontal:hover { background: {{fg_muted}}; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    /* === CARDS === */
    QFrame[class="card"] {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 12px;
        padding: 20px;
    }
    QFrame[class="card-light"] {
        background-color: {{bg_input}};
        border-radius: 8px;
        padding: 8px;
        border: none;
    }

    /* === LABELS === */
    QLabel[class="title"] { font-size: 22px; font-weight: 700; color: {{fg}}; }
    QLabel[class="subtitle"] { font-size: 14px; color: {{fg_muted}}; font-weight: 400; }
    QLabel[class="section"] {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {{fg_muted}};
    }
    QLabel[class="bold"] {
        font-weight: 600;
        color: {{fg}};
    }
    QLabel[class="card-title"] {
        font-size: 14px;
        font-weight: 700;
        color: {{fg}};
    }
    QLabel[class="metric-icon"] {
        font-size: 24px;
    }
    QLabel[class="caption"] {
        font-size: 12px;
        color: {{fg_muted}};
    }
    /* === NUEVAS CLASES: small, micro, small-accent, small-muted === */
    QLabel[class="small"] {
        font-size: 10px;
        color: {{fg_muted}};
        padding: 0;
        background: transparent;
        border: none;
    }
    QLabel[class="micro"] {
        font-size: 9px;
        color: {{fg_muted}};
        padding: 0;
        background: transparent;
        border: none;
    }
    QLabel[class="small-accent"] {
        font-size: 9px;
        color: {{accent}};
        padding: 0;
        background: transparent;
        border: none;
    }
    QLabel[class="small-muted"] {
        font-size: 10px;
        color: {{fg_muted}};
        padding: 0;
        background: transparent;
        border: none;
    }

    QLabel[class="badge-success"] {
        background-color: rgba(52,211,153,0.15);
        color: {{success}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-warning"] {
        background-color: rgba(251,191,36,0.15);
        color: {{warning}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-danger"] {
        background-color: rgba(248,113,113,0.15);
        color: {{danger}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-info"] {
        background-color: rgba(99,102,241,0.15);
        color: {{primary}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    /* === DIVIDER === */
    QFrame[class="divider"] {
        background-color: {{border}};
    }

    /* === CHECKBOX === */
    QCheckBox { spacing: 8px; color: {{fg}}; font-size: 13px; }
    QCheckBox::indicator {
        width: 18px; height: 18px;
        border-radius: 4px;
        border: 1.5px solid {{border}};
        background-color: {{bg_input}};
    }
    QCheckBox::indicator:checked { background-color: {{primary}}; border-color: {{primary}}; }

    /* === RADIO BUTTON === */
    QRadioButton { spacing: 8px; color: {{fg}}; font-size: 13px; }
    QRadioButton::indicator {
        width: 18px; height: 18px;
        border-radius: 9px;
        border: 1.5px solid {{border}};
        background-color: {{bg_input}};
    }
    QRadioButton::indicator:checked { background-color: {{primary}}; border-color: {{primary}}; }

    /* === SLIDER === */
    QSlider::groove:horizontal {
        height: 6px;
        background: {{bg_input}};
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: {{primary}};
        border: none;
        width: 18px; height: 18px;
        border-radius: 9px;
        margin: -6px 0;
    }
    QSlider::sub-page:horizontal { background: {{primary}}; border-radius: 3px; }

    /* === TAB WIDGET === */
    QTabWidget::pane {
        border: 1px solid {{border}};
        border-radius: 12px;
        background-color: {{bg_card}};
        padding: 8px;
    }
    QTabBar::tab {
        background: transparent;
        color: {{fg_muted}};
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-size: 13px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background-color: {{primary_light}}; color: {{primary}}; font-weight: 600; }
    QTabBar::tab:hover:!selected { background-color: {{bg_input}}; color: {{fg}}; }

    /* === PROGRESS BAR === */
    QProgressBar {
        background-color: {{bg_input}};
        border: none;
        border-radius: 999px;
        min-height: 8px;
        text-align: center;
        color: transparent;
    }
    QProgressBar::chunk { background-color: {{primary}}; border-radius: 999px; }

    /* === TOOLTIP === */
    QToolTip {
        background-color: {{bg_card}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 500;
    }

    /* === DIALOGS === */
    QDialog, QFrame#dlgOuter, QFrame[class="dialog-outer"] {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 16px;
    }

    /* === SPLITTER === */
    QSplitter::handle { background-color: {{border}}; width: 1px; }

    /* === MENU === */
    QMenu {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 10px;
        padding: 6px;
    }
    QMenu::item {
        padding: 8px 16px;
        border-radius: 6px;
        color: {{fg}};
        font-size: 13px;
    }
    QMenu::item:selected { background-color: {{primary_light}}; color: {{primary}}; }
    QMenu::separator { height: 1px; background: {{border}}; margin: 4px 8px; }

    /* === STATUS BAR === */
    QStatusBar {
        background-color: {{bg_card}};
        color: {{fg_muted}};
        border-top: 1px solid {{border}};
        font-size: 12px;
        padding: 4px 12px;
    }

    /* === POS VIEW === */
    QPushButton[class="category-button"] {
        background-color: {{bg_input}};
        color: {{fg_muted}};
        border: 1.5px solid {{border}};
        border-radius: 10px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton[class="category-button"]:hover {
        border-color: {{primary}};
        color: {{primary}};
    }
    QPushButton[class="category-button"]:checked {
        background-color: {{primary}};
        color: #ffffff;
        border-color: {{primary}};
        font-weight: 600;
    }
    QScrollArea {
        border: none;
        background: transparent;
    }
    QWidget#scrollAreaWidgetContents {
        background: transparent;
    }
    QFrame[class="product-card"] {
        background-color: {{bg_card}};
        border: 1.5px solid {{border}};
        border-radius: 12px;
    }
    QFrame[class="product-card"]:hover {
        border-color: {{primary}};
        background-color: {{bg_input}};
    }
    QLabel#product-card-icon {
        font-size: 32px;
        border: none;
        background: transparent;
    }
    QLabel#product-card-name {
        font-size: 12px;
        font-weight: 600;
        color: {{fg}};
        border: none;
        background: transparent;
    }
    QLabel#product-card-price {
        font-size: 14px;
        font-weight: 700;
        color: {{accent}};
        border: none;
        background: transparent;
    }

    /* === COMBO CARDS === */
    QFrame[class="combo-card"] {
        background-color: {{bg_card}};
        border: 2px solid {{primary}};
        border-radius: 12px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {{primary_light}},
            stop:1 {{bg_card}});
    }
    QFrame[class="combo-card"]:hover {
        border-color: {{warning}};
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(251,191,36,0.15),
            stop:1 {{bg_card}});
    }
    QLabel#combo-card-icon {
        font-size: 32px;
        border: none;
        background: transparent;
    }
    QLabel#combo-card-name {
        font-size: 12px;
        font-weight: 700;
        color: {{fg}};
        border: none;
        background: transparent;
    }
    QLabel#combo-card-price {
        font-size: 14px;
        font-weight: 700;
        color: {{accent}};
        border: none;
        background: transparent;
    }
    QLabel#combo-savings-badge {
        font-size: 10px;
        padding: 2px 6px;
    }

    /* === ORDER PANEL === */
    QFrame#orderPanel {
        background-color: {{bg_card}};
        border-left: 1px solid {{border}};
    }
    QFrame[class="order-item-card"] {
        background-color: {{bg_input}};
        border: 1px solid {{border}};
        border-radius: 8px;
        padding: 8px;
    }
    QScrollArea#order-items-scroll-area {
        border: none;
        background: transparent;
    }
    QFrame#order-panel-separator {
        background-color: {{border}};
    }
    QLabel#order-panel-total-value {
        font-size: 20px;
        font-weight: 800;
        color: {{accent}};
    }
    QLabel#order-panel-total-row-value {
        font-size: 13px;
        font-weight: 600;
        color: {{fg}};
    }
    QPushButton[class="success"] {
        background-color: {{success}};
        color: #ffffff;
    }
    QPushButton[class="success"]:hover {
        background-color: #10b981;
    }

    /* === REPORTS === */
    QPushButton[class="period-button"] {
        background-color: {{bg_input}};
        color: {{fg_muted}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 6px 20px;
        font-size: 13px;
        font-weight: 500;
        min-height: 24px;
    }
    QPushButton[class="period-button"]:hover {
        border-color: {{primary}};
        color: {{fg}};
    }
    QPushButton[class="period-button"]:checked {
        background-color: {{primary}};
        color: #ffffff;
        border-color: {{primary}};
        font-weight: 600;
    }

    /* === PAYMENT DIALOG === */
    QLabel#payment-total-value {
        color: {{primary}};
    }
    QDoubleSpinBox#payment-amount-input {
        font-size: 18px;
        font-weight: bold;
    }

    /* === PAYMENT DIALOG TABS === */
    QPushButton[class="payment-tab-btn"] {
        background-color: transparent;
        color: {{fg_muted}};
        border: 1.5px solid {{border}};
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: 500;
        border-bottom: none;
    }
    QPushButton[class="payment-tab-btn"]:hover {
        background-color: {{bg_input}};
        color: {{fg}};
    }
    QPushButton[class="payment-tab-btn"]:checked {
        background-color: {{bg_card}};
        color: {{primary}};
        border-color: {{primary}};
        font-weight: 700;
    }

    QFrame[class="payment-method-row"] {
        background-color: {{bg_input}};
        border: 1px solid {{border}};
        border-radius: 8px;
    }
    QFrame[class="payment-method-row"]:hover {
        border-color: {{primary}};
    }

    QPushButton[class="payment-method-btn"] {
        background-color: {{bg_input}};
        color: {{fg_muted}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 500;
    }
    QPushButton[class="payment-method-btn"]:hover {
        border-color: {{primary}};
        color: {{fg}};
    }
    QPushButton[class="payment-method-btn"]:checked {
        background-color: {{primary_light}};
        color: {{primary}};
        border-color: {{primary}};
        font-weight: 700;
    }

    QFrame#progress-bar-bg {
        background-color: {{bg_input}};
        border-radius: 6px;
        border: none;
    }
    QFrame#progress-fill {
        background-color: {{success}};
        border-radius: 6px;
        border: none;
    }
    QLabel#payment-vuelto-success {
        color: {{success}};
    }

    /* === KDS / KITCHEN DISPLAY SYSTEM === */
    QFrame#kds-column {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 12px;
    }
    QFrame#kds-column-header {
        background-color: transparent;
        border-bottom: 1px solid {{border}};
        border-radius: 0px;
    }
    QLabel[class="kds-column-title"] {
        font-size: 15px;
        font-weight: 700;
        color: {{fg}};
    }
    QLabel[class="kds-count-badge"] {
        background-color: {{primary_light}};
        color: {{primary}};
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
    }
    QFrame[class="kds-card"] {
        background-color: {{bg_input}};
        border: 2px solid rgba(52,211,153,0.3);
        border-radius: 12px;
    }
    QFrame[class="kds-card"]:hover {
        border-color: {{primary}};
    }
    QFrame[class="kds-card"][urgency="warning"] {
        border-color: rgba(251,191,36,0.5);
        background-color: rgba(251,191,36,0.05);
    }
    QFrame[class="kds-card"][urgency="critical"] {
        border-color: rgba(248,113,113,0.6);
        background-color: rgba(248,113,113,0.06);
    }
    QLabel[class="kds-order-number"] {
        color: {{fg}};
        font-size: 22px;
        font-weight: 800;
    }
    QLabel[class="kds-type-icon"] {
        font-size: 22px;
        border: none;
        background: transparent;
    }
    QLabel[class="kds-timer"] {
        font-size: 20px;
        font-weight: 800;
        font-family: 'Courier New', monospace;
        color: {{fg}};
    }
    QLabel[class="kds-timer"][urgency="normal"] {
        color: {{success}};
    }
    QLabel[class="kds-timer"][urgency="warning"] {
        color: {{warning}};
    }
    QLabel[class="kds-timer"][urgency="critical"] {
        color: {{danger}};
    }
    QLabel[class="kds-item-text"] {
        font-size: 14px;
        font-weight: 500;
        color: {{fg}};
        padding: 2px 0;
    }
    QLabel[class="kds-note"] {
        font-size: 12px;
        font-style: italic;
        color: {{warning}};
        padding: 4px 8px;
        background-color: rgba(251,191,36,0.1);
        border-radius: 6px;
    }
    QLabel[class="kds-delivery-tag"] {
        font-size: 11px;
        color: {{accent}};
        padding: 2px 8px;
        border: 1px solid {{accent}};
        border-radius: 4px;
        font-weight: 600;
    }
    QLabel[class="kds-empty"] {
        font-size: 14px;
        color: {{fg_muted}};
        padding: 40px 0;
    }
    QPushButton[class="kds-btn-primary"] {
        background-color: {{primary}};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
    }
    QPushButton[class="kds-btn-primary"]:hover {
        background-color: {{primary_hover}};
    }
    QPushButton[class="kds-btn-success"] {
        background-color: {{success}};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
    }
    QPushButton[class="kds-btn-success"]:hover {
        background-color: #10b981;
    }
    QPushButton[class="kds-btn-secondary"] {
        background-color: transparent;
        color: {{fg_muted}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton[class="kds-btn-secondary"]:hover {
        border-color: {{fg}};
        color: {{fg}};
    }
    QPushButton[class="kds-btn-warning"] {
        background-color: rgba(251,191,36,0.15);
        color: {{warning}};
        border: 1.5px solid {{warning}};
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton[class="kds-btn-warning"]:hover {
        background-color: rgba(251,191,36,0.25);
    }
    QFrame[class="kds-items"] {
        background: transparent;
        border: none;
    }
    QLabel[class="kds-clock"] {
        font-size: 16px;
        font-weight: 700;
        color: {{fg_muted}};
        padding: 0 12px;
    }
    QScrollArea#kds-scroll {
        border: none;
        background: transparent;
    }

    /* === SIDEBAR NAV BUTTON (checked) === */
    QPushButton[class="sidebar-nav-button"] {
        background-color: transparent;
        color: {{fg_muted}};
        border: none;
        border-radius: 10px;
        text-align: left;
        padding: 10px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton[class="sidebar-nav-button"]:hover {
        background-color: {{primary_light}};
        color: {{fg}};
    }
    QPushButton[class="sidebar-nav-button"]:checked {
        background-color: {{primary}};
        color: #ffffff;
        font-weight: 600;
    }
    """

    replacements = {
        '{{bg}}': theme.get('bg', '#0f172a'),
        '{{bg_card}}': theme.get('bg_card', '#1e293b'),
        '{{bg_input}}': theme.get('bg_input', '#334155'),
        '{{fg}}': theme.get('fg', '#f1f5f9'),
        '{{fg_muted}}': theme.get('fg_muted', '#94a3b8'),
        '{{primary}}': theme.get('primary', '#6366f1'),
        '{{primary_hover}}': theme.get('primary_hover', '#4f46e5'),
        '{{primary_light}}': theme.get('primary_light', 'rgba(99,102,241,0.12)'),
        '{{border}}': theme.get('border', '#334155'),
        '{{accent}}': theme.get('accent', '#22d3ee'),
        '{{success}}': theme.get('success', '#34d399'),
        '{{warning}}': theme.get('warning', '#fbbf24'),
        '{{danger}}': theme.get('danger', '#f87171'),
        '{{danger_hover}}': theme.get('danger_hover', '#ef4444'),
    }
    for key, val in replacements.items():
        base = base.replace(key, val)
    return base
