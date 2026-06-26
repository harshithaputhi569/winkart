# Winkart Seller Panel — Screen Designs

## Color Palette (Matching User App)
| Token | Value | Usage |
|---|---|---|
| Primary | `#3D5AFE` | Headers, buttons, active states |
| Success | `#00C853` | Active badges, revenue positive |
| Warning | `#FFA000` | Pending orders, amber alerts |
| Error | `#E53935` | Out of stock, delete, logout |
| Background | `#F0F4FF` | Screen background |
| Card | `#FFFFFF` | Cards, panels |

## Navigation
**Bottom Tab Bar** (5 tabs): Dashboard · Products · Orders · Banners · Profile

---

## Screen 1 — Seller Login

```
┌─────────────────────────────────┐
│  🟣 Purple gradient header       │
│  ┌─────────────────────────────┐ │
│  │  [W]  WINKART              │ │
│  │       Seller Panel         │ │
│  └─────────────────────────────┘ │
│                                  │
│  ┌─────────────────────────────┐ │
│  │  📧 Email / Mobile Number  │ │
│  ├─────────────────────────────┤ │
│  │  🔒 Password      [👁]     │ │
│  │                            │ │
│  │        Forgot Password?     │ │
│  │                            │ │
│  │  ┌───────────────────────┐ │ │
│  │  │     LOGIN             │ │ │
│  │  └───────────────────────┘ │ │
│  │                            │ │
│  │  Register as New Seller →  │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Components:** Logo + branding card, email input, password with eye toggle, forgot link, login button, register link.

---

## Screen 2 — Dashboard

```
┌─────────────────────────────────┐
│  [🏪 Electro World]  [🔔] [👤]  │
│                                  │
│  ┌────────┐ ┌────────┐          │
│  │ Orders │ │Revenue │          │
│  │  Today │ │  Today │          │
│  │   48   │ │₹1.24L  │          │
│  └────────┘ └────────┘          │
│  ┌────────┐ ┌────────┐          │
│  │Pending │ │Products│          │
│  │   12   │ │  342   │          │
│  └────────┘ └────────┘          │
│                                  │
│  Recent Orders ─────────────    │
│  ┌────────────────────────────┐ │
│  │ #ORD001  Rahul K  ₹5,490  │ │
│  │ 🟢 Delivered               │ │
│  ├────────────────────────────┤ │
│  │ #ORD002  Priya S  ₹2,199  │ │
│  │ 🟡 Processing              │ │
│  └────────────────────────────┘ │
│                                  │
│  Revenue Chart (Weekly bars)     │
│  ████ ██ ████ ██ ███ ████ ██    │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

**Components:** Header bar, 4 metric cards (2×2 grid), recent orders list with status badges (green/orange/red), revenue bar chart (weekly/monthly toggle).

---

## Screen 3 — Category Management

```
┌─────────────────────────────────┐
│  Categories                 [+] │
│  ┌─────────────────────────┐    │
│  │ 🔍 Search categories... │    │
│  └─────────────────────────┘    │
│                                  │
│  ▼ 📺 Electronics   [342] ✏ 🗑  │
│    ├── 📺 Televisions  [45]     │
│    ├── 🫧 Washing Machines [38] │
│    ├── ❄ Refrigerators   [52]  │
│    └── 🎧 Headphones    [28]   │
│                                  │
│  ▶ 🛋 Furniture      [245] ✏ 🗑 │
│  ▶ ⚡ Electrical     [198] ✏ 🗑 │
│  ▶ 🪟 Tiles          [187] ✏ 🗑 │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

**Add/Edit Bottom Sheet:**
- Category name field
- Parent category dropdown (for sub-categories)
- Category image upload
- Save button

---

## Screen 4 — Product Management

```
┌─────────────────────────────────┐
│  Products                   [+] │
│  ┌─────────────────────────┐    │
│  │ 🔍 Search by name/SKU   │    │
│  └─────────────────────────┘    │
│  [All] [Active] [Inactive] [Out]│
│                                  │
│  ┌────────────────────────────┐ │
│  │ [IMG] Samsung 236L Fridge  │ │
│  │       Electronics  ₹26,990 │ │
│  │       Stock: 12  [●] ✏    │ │
│  ├────────────────────────────┤ │
│  │ [IMG] LG 7kg WM            │ │
│  │       Electronics  ₹24,490 │ │
│  │       Stock: 8   [●] ✏    │ │
│  └────────────────────────────┘ │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

**Add/Edit Product Screen:**
- Product name, description
- Category (Level 1 → Level 2 dropdowns)
- Price + Discount price
- Stock quantity
- Multiple image upload
- Attribute mapping fields
- Save & Publish button

---

## Screen 5 — Banners & Videos Management

```
┌─────────────────────────────────┐
│  Banners & Videos           [+] │
│  [Image Banners] [Video Banners]│
│                                  │
│  ┌────────────────────────────┐ │
│  │ [▓▓▓BANNER PREVIEW▓▓▓▓▓▓] │ │
│  │  Summer Sale Banner        │ │
│  │  12 May – 30 May 2025      │ │
│  │  🟢 Active        ✏ 🗑   │ │
│  ├────────────────────────────┤ │
│  │ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] │ │
│  │  Tech Fest Banner          │ │
│  │  01 Jun – 15 Jun 2025      │ │
│  │  🔴 Scheduled     ✏ 🗑   │ │
│  └────────────────────────────┘ │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

**Add Banner Bottom Sheet:**
- Upload image / video file
- Banner title
- Start date picker + End date picker
- Target link or product selection
- Preview → Save button

---

## Screen 6 — Bills / Orders Management

```
┌─────────────────────────────────┐
│  Orders                         │
│  ┌─────────────────────────┐    │
│  │ 🔍 Search orders...     │    │
│  └─────────────────────────┘    │
│  [All] [Pending] [Delivered] [Cancelled]│
│                                  │
│  ┌────────────────────────────┐ │
│  │ #ORD001   12 May 2025      │ │
│  │ Rahul Kumar  +91 98765...  │ │
│  │ 3 items  •  ₹70,970        │ │
│  │ 🟢 Delivered       View →  │ │
│  ├────────────────────────────┤ │
│  │ #ORD002   11 May 2025      │ │
│  │ Priya Singh  +91 87654...  │ │
│  │ 1 item   •  ₹5,490         │ │
│  │ 🟡 Processing     View →  │ │
│  └────────────────────────────┘ │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

---

## Screen 7 — Upselling / Cross-selling Configuration

```
┌─────────────────────────────────┐
│  Upsell & Cross-sell            │
│  [Upsell Products] [Cross-sell] │
│                                  │
│  Source Product                  │
│  ┌─────────────────────────┐    │
│  │ 🔍 Search base product  │    │
│  └─────────────────────────┘    │
│  Selected: Samsung Fridge ×     │
│                                  │
│  Linked Products (3)             │
│  ┌────────────────────────────┐ │
│  │ [IMG] LG WM      ₹24,490  │ │
│  │                  Remove × │ │
│  ├────────────────────────────┤ │
│  │ [IMG] Sony TV    ₹32,990  │ │
│  │                  Remove × │ │
│  └────────────────────────────┘ │
│                                  │
│  [+ Add Products]                │
│  [Save Configuration]           │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

---

## Screen 8 — Import / Export

```
┌─────────────────────────────────┐
│  Import & Export                │
│                                  │
│  ── IMPORT ──────────────────   │
│  ┌────────────────────────────┐ │
│  │ ⬆ Upload Excel (.xlsx)    │ │
│  │ ↓ Download Sample Template │ │
│  │                            │ │
│  │ Column Mapping Preview     │ │
│  │ Name | SKU | Price | Stock │ │
│  │ ─────────────────────────  │ │
│  │ [Import Now]               │ │
│  └────────────────────────────┘ │
│                                  │
│  ── EXPORT ──────────────────   │
│  Product Type ▾  Date Range     │
│  Format: Excel / CSV            │
│  [Export Now]                   │
│                                  │
│  Import History                 │
│  products_may.xlsx  12/5  ✅    │
│  products_apr.xlsx  01/4  ⚠    │
│                                  │
│ [Dashboard][Products][Orders][Banners][Profile] │
└─────────────────────────────────┘
```

---

## Screen 9 — Seller Profile / Shop Settings

```
┌─────────────────────────────────┐
│  Shop Settings                  │
│                                  │
│  ┌────────────────────────────┐ │
│  │  [🏪]  Electro World       │ │
│  │        Rajesh Kumar        │ │
│  │        +91 98765 43210     │ │
│  │        rajesh@email.com    │ │
│  └────────────────────────────┘ │
│                                  │
│  Shop Description                │
│  [Electronics & home appliances] │
│                                  │
│  Shop Address                    │
│  [Siripuram Junction, Vizag...]  │
│                                  │
│  [MAP LOCATION PREVIEW]          │
│                                  │
│  Business Hours                  │
│  Mon ──────────── 9AM–9PM [●]   │
│  Tue ──────────── 9AM–9PM [●]   │
│  Sun ──────────── Closed  [○]   │
│                                  │
│  Change Password  Notifications  │
│  🔴 Logout                       │
│                                  │
│  [Save Changes]                  │
└─────────────────────────────────┘
```

---

## Navigation Summary

| Tab | Screen |
|---|---|
| 🏠 Dashboard | Metrics, recent orders, chart |
| 📦 Products | Product list → Add/Edit product |
| 📋 Orders | Order list → Order detail |
| 🖼 Banners | Banner/Video list → Add banner |
| 👤 Profile | Shop settings |

> [!IMPORTANT]
> These seller screens will be built as a **separate React Native app** or as a **separate navigator stack** within the same app, gated by role-based login.
