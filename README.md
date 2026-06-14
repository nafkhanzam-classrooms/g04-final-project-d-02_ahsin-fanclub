# Snake.io — Multiplayer Arena

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/4SHtB1vz)

**Final Project — Pemrograman Jaringan**

Implementasi game multiplayer Snake.io berbasis WebSocket dengan arsitektur client-server yang menggunakan simulasi fisika di sisi server (server-authoritative) dan interpolasi posisi di sisi client.

---

## Daftar Isi

1. [Deskripsi Proyek](#1-deskripsi-proyek)
2. [Tech Stack](#2-tech-stack)
3. [Fitur Utama](#3-fitur-utama)
4. [Arsitektur Sistem](#4-arsitektur-sistem)
5. [Struktur Folder](#5-struktur-folder)
6. [Penjelasan Komponen Penting](#6-penjelasan-komponen-penting)
7. [Cara Menjalankan Proyek](#7-cara-menjalankan-proyek)
8. [Kesimpulan](#8-kesimpulan)

---

## 1. Deskripsi Proyek

### Tujuan Proyek

Proyek ini merupakan implementasi game multiplayer Snake.io — sebuah permainan arena di mana 2 hingga 4 pemain mengendalikan ular secara bersamaan dalam satu dunia game bersama. Setiap pemain berusaha memakan makanan untuk memanjangkan ular mereka, sekaligus menghindari tabrakan dengan ular pemain lain maupun batas arena.

Proyek ini dibuat sebagai implementasi nyata konsep-konsep jaringan komputer, meliputi:
- Komunikasi full-duplex berbasis WebSocket
- Protokol biner menggunakan MessagePack
- Arsitektur client-server dengan simulasi otoritatif di sisi server
- Sinkronisasi state game melalui snapshot broadcasting
- Teknik networking lanjutan seperti interpolasi posisi dan prediksi client-side

### Gambaran Umum Cara Kerja Sistem

Secara garis besar, sistem bekerja sebagai berikut:

1. Client terhubung ke server via WebSocket pada port 8765.
2. Pemain memilih mode permainan: Quickplay (matchmaking otomatis) atau Create/Join Room (private room).
3. Server mengumpulkan pemain yang cukup, kemudian memulai hitung mundur 3 detik.
4. Simulasi game berjalan sepenuhnya di server dengan tick rate 30 tick per detik.
5. Setiap tick, server mengirimkan snapshot state game ke seluruh pemain dalam room.
6. Client menerima snapshot dan menginterpolasinya untuk menghasilkan rendering mulus pada 60 FPS.
7. Pemain menggerakkan mouse dan arah dikirimkan ke server sebagai input.
8. Match berakhir ketika hanya satu ular yang tersisa, atau ketika timer 180 detik habis.

---

## 2. Tech Stack

### Bahasa Pemrograman

| Komponen | Bahasa | Versi |
|----------|--------|-------|
| Server   | Python | 3.11+ |
| Client   | Python | 3.11+ |

### Framework dan Library

| Library      | Kegunaan                                           |
|--------------|----------------------------------------------------|
| `websockets` | Implementasi WebSocket server dan client (async)   |
| `msgpack`    | Serialisasi biner pesan jaringan                   |
| `pygame-ce`  | Rendering grafis client, pengelolaan input, audio  |
| `asyncio`    | Event loop asinkron untuk concurrency              |

### Teknologi Networking

| Teknologi                   | Detail                                                      |
|-----------------------------|-------------------------------------------------------------|
| WebSocket                   | Protokol komunikasi full-duplex (RFC 6455)                  |
| MessagePack                 | Format serialisasi biner pengganti JSON yang lebih ringkas  |
| Asyncio                     | Cooperative multitasking untuk server single-thread         |
| Sliding Window Rate Limiter | Pembatasan maksimal 60 pesan per detik per client           |

### Konfigurasi Server

| Parameter             | Nilai             |
|-----------------------|-------------------|
| Host                  | `168.144.139.241` |
| Port                  | `8765`            |
| Server Tick Rate      | 30 tick/detik     |
| Ukuran Pesan Maksimum | 1 MiB             |
| Durasi Match          | 180 detik         |
| Pemain per Room       | 2 hingga 4 pemain |

Server telah di-deploy pada VPS dengan IP publik `168.144.139.241`. Client dapat langsung terhubung ke server tersebut tanpa perlu menjalankan server secara lokal.

---

## 3. Fitur Utama

### Mode Permainan

**Quickplay (Matchmaking Otomatis)**

Pemain bergabung ke antrian matchmaking dan server secara otomatis membentuk room begitu minimal 2 pemain tersedia. Terdapat timeout 10 detik untuk mengisi room yang belum penuh sebelum pertandingan dimulai secara paksa.

**Private Room**

Pemain dapat membuat room private dan mendapatkan kode room 6 digit unik. Pemain lain bergabung menggunakan kode tersebut. Host room memiliki kontrol penuh untuk memulai pertandingan kapan pun jumlah pemain sudah mencukupi.

### Networking dan Sinkronisasi

**Server-Authoritative Simulation**

Seluruh logika game (pergerakan, kolisi, skor) dijalankan di sisi server. Client hanya menerima snapshot state game dan menampilkannya, sehingga tidak ada kemungkinan manipulasi dari sisi client.

**Snapshot Broadcasting**

Server mem-broadcast state game lengkap (posisi semua ular dan makanan) setiap tick ke seluruh pemain dalam room. Setiap snapshot mengandung `local_player_id` sehingga setiap client dapat mengidentifikasi ular miliknya sendiri.

**Snapshot Interpolation (Client-Side)**

Client menerima snapshot pada sekitar 30 Hz tetapi merender pada 60 FPS. Sistem interpolasi menghitung posisi entitas di antara dua snapshot yang berurutan menggunakan linear blending dengan delay 100 ms untuk menyerap jitter jaringan.

**Client-Side Prediction**

Ketika pemain menggerakkan mouse, perubahan arah langsung diterapkan secara lokal pada rendering tanpa menunggu konfirmasi server. Hal ini membuat kontrol terasa responsif meskipun ada latensi jaringan.

**Ping dan RTT Measurement**

Client mengirim pesan `ping` setiap 2 detik ke server dan mengukur waktu round-trip ketika menerima `pong`. Nilai ping ditampilkan pada HUD selama permainan berlangsung.

### Mekanik Game

**Pergerakan Ular**

Ular bergerak maju secara kontinu dengan kecepatan tetap 120 unit per detik. Pemain mengarahkan ular menggunakan posisi kursor mouse. Sistem smooth turning memastikan ular tidak bisa berputar secara instan, melainkan berbelok dengan laju maksimum 200 derajat per detik.

**Sistem Makanan**

Arena mempertahankan 200 item makanan secara konstan. Setiap makanan yang dimakan meningkatkan skor (+10 poin) dan panjang ular (+1 segmen). Ketika ular mati, sebagian segmen tubuhnya (50%) berubah menjadi makanan yang dapat dimakan pemain lain.

**Deteksi Kolisi**

Tiga jenis kolisi dideteksi server setiap tick:
1. Kepala vs Batas Arena — ular yang melewati batas langsung mati.
2. Kepala vs Badan Ular Lain — ular yang menabrak badan ular lain mati.
3. Kepala vs Kepala (Head-on) — kedua ular mati sekaligus (mutual kill).

**Kondisi Kemenangan**

Match berakhir dengan dua kondisi:
- Satu Pemain Tersisa: Pemain terakhir yang masih hidup memenangkan pertandingan.
- Timer Habis (180 detik): Pemain dengan skor tertinggi di antara yang masih hidup dinyatakan menang.

### Antarmuka Client

**Scene Management**

Client menggunakan arsitektur scene berbasis state machine. Setiap layar (menu, matchmaking, lobby, gameplay, results) merupakan scene tersendiri yang mengelola event input dan renderingnya sendiri.

**Kamera dengan Smooth Follow**

Kamera mengikuti kepala ular lokal dengan interpolasi lerp (kecepatan 6.0). Terdapat dead zone radius 20 piksel di tengah layar sehingga kamera tidak gemetar ketika ular hampir diam.

**HUD (Heads-Up Display)**

Selama permainan berlangsung, HUD menampilkan: waktu sisa pertandingan, skor pemain saat ini, peringkat pemain berdasarkan skor, nilai ping, dan nilai FPS saat ini.

**Rate Limiting Input**

Tidak semua perubahan arah mouse dikirim ke server. Input hanya dikirim jika perubahan sudut lebih dari atau sama dengan 2 derajat dan interval pengiriman minimal 1/30 detik. Mekanisme ini mengurangi beban jaringan secara signifikan.

---

## 4. Arsitektur Sistem

### Lapisan Komponen

Sistem terdiri dari tiga lapisan utama yang berkomunikasi melalui WebSocket:

**Lapisan Client** (Pygame + asyncio)

Client terdiri dari komponen-komponen berikut:
- `GameApp` — controller utama yang mengelola window, clock, dan semua subsistem
- `SceneManager` — state machine yang mengatur perpindahan antar scene
- `WebSocketClient` — mengelola koneksi ke server, mengirim pesan, dan menerima data secara async
- `EventDispatcher` — meneruskan pesan yang diterima dari server ke scene yang aktif
- `SnapshotInterpolator` dan `SnapshotBuffer` — menerima dan menginterpolasikan snapshot antar tick
- `Renderer` dan `Camera` — menggambar state game ke layar
- `HUD` — menampilkan informasi permainan secara overlay

**Lapisan Jaringan**

Komunikasi menggunakan protokol WebSocket dengan payload dienkode dalam format MessagePack (biner). Semua pesan — baik dari client ke server maupun sebaliknya — melewati proses encode dan decode MessagePack.

**Lapisan Server** (asyncio)

Server terdiri dari tiga sub-lapisan:
- Networking Layer: `WebSocketServer`, `ConnectionManager`, `MessageRouter`, `RateLimiter`
- Matchmaking dan Room Layer: `MatchmakingService`, `QueueManager`, `RoomAllocator`, `RoomManager`, `Room`, `PlayerSession`
- Simulation Layer: `GameWorld` yang mengkomposisikan tujuh sistem simulasi independen

### Protokol Pesan

Semua pesan menggunakan format MessagePack (biner) yang dikirim melalui koneksi WebSocket.

**Pesan Client ke Server**

| Tipe Pesan     | Parameter Utama                   | Keterangan                                |
|----------------|-----------------------------------|-------------------------------------------|
| `join_queue`   | `username: str`                   | Bergabung ke antrian matchmaking otomatis |
| `cancel_queue` | —                                 | Membatalkan antrian matchmaking           |
| `create_room`  | `username: str`                   | Membuat private room baru                |
| `join_room`    | `username: str`, `room_code: str` | Bergabung ke private room dengan kode    |
| `start_room`   | —                                 | Host memulai pertandingan di lobby       |
| `leave_room`   | —                                 | Meninggalkan room saat ini               |
| `input`        | `direction: float`                | Mengirim arah ular dalam satuan derajat  |
| `ping`         | —                                 | Request pengukuran latensi               |

**Pesan Server ke Client**

| Tipe Pesan          | Parameter Utama                                               | Keterangan                             |
|---------------------|---------------------------------------------------------------|----------------------------------------|
| `queue_status`      | `players_waiting: int`                                        | Update jumlah pemain di antrian        |
| `match_found`       | `room_id: str`, `player_count: int`                           | Match ditemukan, hitung mundur dimulai |
| `match_start`       | `room_id: str`                                                | Pertandingan resmi dimulai             |
| `room_state`        | `room_id`, `state`, `players[]`, `can_start`                  | State lobby terkini                    |
| `snapshot`          | `tick`, `time_left`, `snakes[]`, `foods[]`, `local_player_id` | State game setiap tick                 |
| `player_eliminated` | `player_id: int`                                              | Notifikasi pemain tereliminasi         |
| `match_end`         | `winner_id`, `winner_name`, `rankings[]`                      | Hasil akhir pertandingan               |
| `pong`              | —                                                             | Balasan ping                           |
| `error`             | `message: str`                                                | Pesan error dari server                |

---

## 5. Struktur Folder

```
g04-final-project-d-02_ahsin-fanclub/
|
+-- requirements.txt              # Daftar dependensi Python
|
+-- client/                       # Seluruh kode aplikasi client (Pygame)
|   +-- main.py                   # Entry point client
|   +-- game/
|       +-- game_app.py           # Controller utama: window, clock, subsystem
|       +-- scene_manager.py      # State machine untuk manajemen scene
|       |
|       +-- networking/           # Modul jaringan sisi client
|       |   +-- websocket_client.py   # Koneksi WebSocket async, ping loop
|       |   +-- protocol.py           # Fungsi encode dan decode pesan client
|       |   +-- event_dispatcher.py   # Pub/sub dispatcher untuk event jaringan
|       |   +-- snapshot_buffer.py    # Buffer snapshot terurut dengan timestamp
|       |
|       +-- rendering/            # Modul rendering dan visual
|       |   +-- renderer.py       # Menggambar grid, arena, ular, dan makanan
|       |   +-- camera.py         # Kamera smooth-follow dengan dead zone
|       |   +-- interpolation.py  # Interpolasi linear antar dua snapshot server
|       |
|       +-- scenes/               # Semua layar dalam game
|       |   +-- menu_scene.py         # Menu utama (play, create, join, quit)
|       |   +-- matchmaking_scene.py  # Layar tunggu antrian matchmaking
|       |   +-- loading_scene.py      # Layar hitung mundur sebelum match
|       |   +-- lobby_scene.py        # Lobby private room
|       |   +-- create_room_scene.py  # Layar pembuatan private room
|       |   +-- gameplay_scene.py     # Layar permainan utama
|       |   +-- results_scene.py      # Layar hasil akhir pertandingan
|       |   +-- join_room_modal.py    # Modal input kode room
|       |
|       +-- entities/             # Data class entitas game sisi client
|       |   +-- snake.py          # Data ular: posisi, segmen, skor, status
|       |   +-- food.py           # Data makanan: koordinat
|       |
|       +-- ui/                   # Komponen antarmuka pengguna
|       |   +-- widgets.py        # Button, Label, TextBox reusable
|       |   +-- hud.py            # Heads-Up Display (skor, waktu, ping, FPS)
|       |
|       +-- assets/
|           +-- fonts/            # Aset font
|           +-- sounds/           # Aset audio
|
+-- server/                       # Seluruh kode aplikasi server
    +-- main.py                   # Entry point server
    |
    +-- networking/               # Layer jaringan server
    |   +-- websocket_server.py   # WebSocket server utama, handler koneksi
    |   +-- connection_manager.py # Registry player ID ke WebSocket connection
    |   +-- message_router.py     # Routing pesan ke handler berdasarkan tipe
    |   +-- packet_encoder.py     # Serialisasi dict ke msgpack bytes
    |   +-- packet_decoder.py     # Deserialisasi bytes ke dict
    |   +-- rate_limiter.py       # Sliding-window rate limiter per pemain
    |   +-- protocol.py           # Re-ekspor tipe pesan valid
    |
    +-- matchmaking/              # Sistem matchmaking otomatis
    |   +-- matchmaking_service.py  # Orkestrasi antrian dan alokasi room
    |   +-- queue_manager.py        # Manajemen antrian pemain (FIFO)
    |   +-- room_allocator.py       # Logika penentuan ukuran room
    |
    +-- rooms/                    # Manajemen room dan sesi game
    |   +-- room.py               # Objek Room: lifecycle, game loop, broadcast
    |   +-- room_manager.py       # Registry dan operasi CRUD seluruh room aktif
    |   +-- player_session.py     # State setiap pemain (nama, room, status)
    |
    +-- simulation/               # Mesin simulasi game server-side
    |   +-- game_world.py         # Fasade publik yang mengkomposisikan semua sistem
    |   +-- entities/
    |   |   +-- snake.py          # Entitas ular (posisi, segmen, kecepatan, status)
    |   |   +-- snake_segment.py  # Satu segmen tubuh ular
    |   |   +-- food.py           # Entitas makanan
    |   |   +-- player.py         # Entitas pemain (referensi ke Snake)
    |   +-- systems/
    |   |   +-- movement_system.py       # Pergerakan maju dan smooth turning
    |   |   +-- collision_system.py      # Deteksi kolisi batas dan antar ular
    |   |   +-- food_system.py           # Spawning dan deteksi konsumsi makanan
    |   |   +-- scoring_system.py        # Update skor dan panjang saat makan
    |   |   +-- elimination_system.py    # Proses kematian dan spawn death food
    |   |   +-- timer_system.py          # Hitung mundur durasi match (180 detik)
    |   |   +-- win_condition_system.py  # Deteksi kondisi akhir game
    |   +-- snapshots/
    |       +-- snapshot_generator.py   # Serialisasi state world ke dict snapshot
    |
    +-- events/                   # Sistem event internal server
    |   +-- event_bus.py          # Async pub/sub event bus
    |   +-- event_types.py        # Definisi tipe event internal
    |
    +-- shared/                   # Konstanta dan schema yang digunakan server
        +-- constants.py          # Semua parameter game (tick rate, ukuran world, dll.)
        +-- schemas.py            # Dataclass payload pesan dan enum tipe pesan
```

---

## 6. Penjelasan Komponen Penting

### 6.1 Modul Networking (Server)

**`websocket_server.py` — Inti Server**

Komponen pusat yang mengawasi seluruh koneksi WebSocket. Setiap koneksi baru mendapatkan ID pemain unik yang terus meningkat secara monoton. Server berjalan dalam event loop `asyncio` yang kooperatif, sehingga banyak koneksi dapat dilayani dalam satu thread tanpa blocking.

Handler yang terdaftar: `join_queue`, `cancel_queue`, `create_room`, `join_room`, `start_room`, `leave_room`, `input`, `ping`. Ketika koneksi terputus, server secara otomatis membersihkan antrian matchmaking, room, dan registry koneksi yang terkait.

**`connection_manager.py` — Registry Koneksi**

Memetakan `player_id` (integer yang terus meningkat) ke objek `ServerConnection` WebSocket. Menyediakan metode `send_to(player_id, data)`, `send_to_many(player_ids, data)`, dan `broadcast(data)`. Semua pengiriman melewati `packet_encoder.py` untuk dikonversi ke msgpack sebelum dikirim melalui WebSocket.

**`rate_limiter.py` — Pembatasan Laju**

Mengimplementasikan algoritma sliding-window per pemain. Setiap pemain diizinkan mengirim maksimal 60 pesan per detik. Pesan yang melebihi batas di-drop secara senyap. Batas ini dikonfigurasi via `RATE_LIMIT_MAX_MESSAGES` dan `RATE_LIMIT_WINDOW` di `constants.py`.

**`packet_encoder.py` dan `packet_decoder.py` — Serialisasi**

Semua pesan dienkode dengan MessagePack (`msgpack.packb`) dan didekode dengan `msgpack.unpackb`. Decoder melakukan validasi tipe eksplisit: hasil decode harus berupa `dict`, jika tidak maka `DecodeError` dilempar dan pesan dibuang.

---

### 6.2 Matchmaking

**Alur Kerja Matchmaking**

Ketika pemain mengirim `join_queue`, `MatchmakingService` memanggil `QueueManager.enqueue(player_id)`. Jika antrian mencapai jumlah minimal pemain (`MIN_PLAYERS_PER_ROOM = 2`), `RoomAllocator` menentukan ukuran room yang akan dibuat. `RoomManager.create_room(player_ids)` dipanggil, kemudian `room.start_countdown()` dijadwalkan sebagai asyncio task. Server mengirim `match_found` ke semua pemain di room, menunggu 3 detik, lalu mengirim `match_start` dan memulai game loop.

**`matchmaking_service.py`**

Mengorkestrasikan seluruh pipeline matchmaking dengan menghubungkan `QueueManager`, `RoomAllocator`, dan `RoomManager`. Bertanggung jawab mengirimkan broadcast `queue_status` ke semua pemain yang mengantri setiap kali terjadi perubahan jumlah antrian.

**`queue_manager.py`**

Mengelola antrian pemain menggunakan struktur gabungan set (untuk mencegah duplikasi) dan list (untuk mempertahankan urutan FIFO). Mendukung operasi `enqueue(player_id)`, `dequeue(n)`, dan `remove(player_id)`.

**`room_allocator.py`**

Menentukan kapan room harus dibuat (`should_create_room`) dan berapa banyak pemain yang dimasukkan ke satu room (`get_room_size`) berdasarkan ukuran antrian saat ini dan konstanta batas pemain.

---

### 6.3 Room dan Game Loop

**`room.py` — Siklus Hidup Match**

Room memiliki empat state yang berjalan secara berurutan:
- `WAITING` — Menunggu pemain bergabung (untuk private room).
- `STARTING` — Hitung mundur 3 detik setelah match ditemukan.
- `RUNNING` — Game loop aktif berjalan sebagai asyncio Task.
- `FINISHED` — Match berakhir, room akan dihancurkan oleh RoomManager.

Game loop berjalan dengan fixed timestep 1/30 detik. Setiap iterasi melakukan empat langkah berurutan:

```python
while state == RUNNING:
    tick_start = time.monotonic()

    game_world.update(TICK_INTERVAL)      # Jalankan satu tick simulasi
    check_eliminations()                   # Kirim notifikasi eliminasi ke semua pemain
    check_win_condition()                  # Periksa apakah match sudah berakhir
    broadcast_snapshot_to_all_players()   # Kirim snapshot state game ke semua pemain

    sleep(TICK_INTERVAL - elapsed)        # Tidur sisa waktu agar tick rate stabil
```

---

### 6.4 Simulasi Game (Server-Side)

`GameWorld` adalah fasade publik yang mengkomposisikan tujuh sistem independen. Setiap sistem dipanggil secara berurutan dalam satu pemanggilan `update(dt)`:

| Urutan | Sistem               | Fungsi                                                                      |
|--------|----------------------|-----------------------------------------------------------------------------|
| 1      | `MovementSystem`     | Menggerakkan ular maju dan menerapkan smooth turning (maks. 200 derajat/detik) |
| 2      | `FoodSystem`         | Mendeteksi konsumsi makanan berdasarkan jarak kepala ke food item            |
| 3      | `ScoringSystem`      | Menambah skor (+10) dan panjang (+1 segmen) saat makanan dimakan             |
| 4      | `CollisionSystem`    | Mendeteksi kolisi batas arena, kepala vs badan, dan kepala vs kepala         |
| 5      | `EliminationSystem`  | Mematikan ular yang terkena kolisi dan men-spawn death food                  |
| 6      | `FoodSystem`         | Mempertahankan jumlah makanan agar tetap 200 item                            |
| 7      | `TimerSystem`        | Mengurangi waktu tersisa dan menandai timer sebagai expired                  |

`CollisionSystem` mendeteksi tiga jenis kolisi: kepala melewati batas world (`WORLD_WIDTH x WORLD_HEIGHT = 4000x4000`), kepala menyentuh segmen badan ular lain (menggunakan radius check), dan dua kepala saling bertabrakan (mutual kill). Deteksi head-on dilakukan dalam pass terpisah agar tidak bergantung pada urutan iterasi.

**Entitas Simulasi**

`Snake` menyimpan posisi kepala `(x, y)`, `direction` (arah aktual dalam derajat), `target_direction` (arah yang diminta oleh pemain), `speed`, `length`, `score`, dan `segments` (deque berisi posisi setiap segmen). `Food` hanya menyimpan koordinat `(x, y)`.

---

### 6.5 Sinkronisasi Data — Interpolasi Client

Server mengirimkan snapshot pada 30 Hz (setiap kurang lebih 33 ms), sementara client merender pada 60 FPS (setiap kurang lebih 16 ms). Tanpa interpolasi, rendering akan terlihat patah-patah karena posisi entitas hanya diperbarui setiap dua frame.

Solusi yang diimplementasikan adalah snapshot interpolation dengan delay 100 ms:

- Setiap snapshot yang diterima disimpan di `SnapshotBuffer` dengan timestamp penerimaan lokal (`time.monotonic()`).
- Pada setiap frame render, dihitung `render_time = now - 0.100` (100 ms di masa lalu).
- Dicari dua snapshot A dan B yang mengapit `render_time`, kemudian dihitung `alpha = (render_time - A.time) / (B.time - A.time)`.
- Posisi setiap entitas dihitung dengan `pos = A.pos + (B.pos - A.pos) * alpha`.

Arah ular diinterpolasikan menggunakan shortest-arc angle interpolation untuk menghindari rotasi yang memutar melalui jalur panjang saat nilai sudut melewati batas 0/360 derajat. `SnapshotBuffer` menampung maksimal 30 snapshot dan secara otomatis membuang snapshot yang datang terlambat atau duplikat.

Client-side prediction diterapkan di atas interpolasi: ketika pemain mengubah arah, `SnapshotInterpolator.set_predicted_direction(angle)` dipanggil sehingga arah lokal langsung diperbarui pada rendering tanpa menunggu konfirmasi snapshot berikutnya dari server.

---

### 6.6 Event Dispatcher (Client)

`EventDispatcher` mengimplementasikan pola publish-subscribe sederhana di sisi client. Setiap scene mendaftarkan handler untuk event tertentu saat `enter()` dipanggil dan melepasnya saat `exit()` dipanggil. Ketika `WebSocketClient._recv_loop()` menerima pesan, ia memanggil `dispatcher.dispatch(msg["type"], msg)` yang meneruskannya ke semua handler yang terdaftar untuk tipe pesan tersebut.

Contoh pemetaan event ke handler:
- `"snapshot"` diteruskan ke `GameplayScene._on_snapshot()`
- `"match_end"` diteruskan ke `GameplayScene._on_match_end()`
- `"room_state"` diteruskan ke `LobbyScene._on_room_state()`
- `"error"` diteruskan ke handler error masing-masing scene

---

### 6.7 Camera dan Rendering

`Camera` mengimplementasikan smooth follow dengan lerp. Kamera hanya mulai bergerak ketika target (kepala ular pemain) keluar dari dead zone radius 20 piksel. Metode `world_to_screen(wx, wy)` dan `screen_to_world(sx, sy)` digunakan secara konsisten di seluruh modul rendering dan input untuk mengkonversi antara koordinat world game dan koordinat piksel layar.

`Renderer` menggunakan frustum culling untuk makanan: item makanan yang berada di luar visible rect kamera tidak digambar, menghemat operasi draw yang tidak diperlukan. Setiap ular digambar dengan warna unik berdasarkan `snake.id % len(SNAKE_COLORS)`, dengan efek fade pada segmen tubuh (warna semakin gelap ke arah ekor) dan detail mata pada kepala.

---

## 7. Cara Menjalankan Proyek

### Prasyarat

- Python 3.11 atau lebih baru
- pip (package manager Python)

### Instalasi Dependensi

Dari direktori root proyek, jalankan:

```bash
pip install -r requirements.txt
```

Library yang akan diinstal: `websockets`, `msgpack`, `pygame-ce`, `pygame`.

### Menggunakan Server yang Sudah Di-deploy (Direkomendasikan)

Server sudah berjalan pada VPS dengan IP `168.144.139.241` di port `8765`. Untuk menggunakan server tersebut, ubah konstanta `DEFAULT_SERVER_URI` di `client/game/networking/websocket_client.py`:

```python
DEFAULT_SERVER_URI = "ws://168.144.139.241:8765"
```

Kemudian jalankan client dari direktori `client/`:

```bash
cd client
python main.py
```

### Menjalankan Server Secara Lokal

Jika ingin menjalankan server sendiri, buka terminal di direktori root proyek dan jalankan:

```bash
# Metode 1: Menggunakan module runner (direkomendasikan)
python -m server.main

# Metode 2: Langsung
python server/main.py
```

Server akan menampilkan log berikut saat berhasil berjalan:

```
HH:MM:SS [INFO] __main__: Starting Snake.io server on ws://0.0.0.0:8765
HH:MM:SS [INFO] server.networking.websocket_server: WebSocket server started on ws://0.0.0.0:8765
```

Tekan Ctrl+C untuk menghentikan server. Server akan melakukan graceful shutdown dan membersihkan semua room yang aktif.

Pastikan `DEFAULT_SERVER_URI` pada client mengarah ke `ws://localhost:8765` saat menggunakan server lokal.

### Menjalankan Client

Buka terminal baru, pindah ke direktori `client/`, lalu jalankan:

```bash
cd client
python main.py
```

Catatan: Client harus dijalankan dari dalam direktori `client/` karena import modul `game.*` bersifat relatif terhadap direktori tersebut.

### Menjalankan Multiple Client

Untuk menguji multiplayer, buka beberapa terminal dan jalankan `python main.py` di masing-masing terminal dari direktori `client/`. Setiap instance akan membuka jendela Pygame tersendiri dan terhubung ke server yang sama.

### Konfigurasi Server

Semua parameter server dapat diubah di `server/shared/constants.py`:

| Konstanta                 | Default   | Keterangan                                    |
|---------------------------|-----------|-----------------------------------------------|
| `WEBSOCKET_HOST`          | `0.0.0.0` | Host server WebSocket                         |
| `WEBSOCKET_PORT`          | `8765`    | Port server WebSocket                         |
| `SERVER_TICK_RATE`        | `30`      | Frekuensi tick simulasi (tick/detik)          |
| `MIN_PLAYERS_PER_ROOM`    | `2`       | Minimal pemain untuk memulai matchmaking      |
| `MAX_PLAYERS_PER_ROOM`    | `4`       | Kapasitas maksimal room                       |
| `MATCHMAKING_FILL_TIMEOUT`| `10.0`    | Detik tunggu sebelum room dimulai otomatis    |
| `MATCH_DURATION`          | `180`     | Durasi match dalam detik                      |
| `MATCH_START_COUNTDOWN`   | `3.0`     | Hitung mundur sebelum match dimulai           |
| `WORLD_WIDTH`             | `4000`    | Lebar arena game (unit)                       |
| `WORLD_HEIGHT`            | `4000`    | Tinggi arena game (unit)                      |
| `TARGET_FOOD_COUNT`       | `200`     | Jumlah makanan yang dipertahankan di arena    |
| `SNAKE_BASE_SPEED`        | `120.0`   | Kecepatan dasar ular (unit/detik)             |
| `SNAKE_TURN_RATE`         | `200.0`   | Kecepatan berbelok ular (derajat/detik)       |
| `RATE_LIMIT_MAX_MESSAGES` | `60`      | Pesan maksimum per detik per pemain           |

### Alur Penggunaan Aplikasi

1. Pastikan server berjalan (lokal atau gunakan server VPS yang sudah di-deploy).
2. Jalankan client dari direktori `client/`.
3. Ketik username pada kolom teks di menu utama.
4. Pilih mode permainan:
   - QUICKPLAY — masuk ke antrian matchmaking otomatis.
   - CREATE ROOM — buat room private, bagikan kode 6 digit kepada teman.
   - JOIN ROOM — masukkan kode room dari teman untuk bergabung.
5. Tunggu hitung mundur 3 detik.
6. Gerakkan mouse untuk mengarahkan ular selama permainan berlangsung.
7. Setelah match berakhir, layar hasil menampilkan peringkat dan skor semua pemain.

---

## 8. Kesimpulan

### Ringkasan Implementasi

Proyek ini berhasil mengimplementasikan game multiplayer real-time lengkap dengan arsitektur yang mengikuti praktik terbaik pengembangan game online:

1. **Server-Authoritative Architecture** — Seluruh logika game dijalankan di server, mencegah manipulasi dari sisi client.
2. **Efisiensi Protokol** — Penggunaan MessagePack sebagai format serialisasi biner mengurangi overhead dibandingkan JSON, hal yang krusial untuk broadcast snapshot 30 kali per detik.
3. **Smooth Rendering** — Implementasi interpolasi snapshot dengan delay 100 ms menghasilkan animasi 60 FPS yang halus meskipun server hanya mengirim update pada 30 Hz.
4. **Responsivitas Input** — Client-side prediction memastikan kontrol terasa langsung responsif tanpa menunggu konfirmasi server.
5. **Concurrency yang Bersih** — Penggunaan `asyncio` secara konsisten di server dan client memungkinkan penanganan banyak koneksi secara bersamaan dalam satu thread.
6. **Arsitektur Modular** — Pemisahan yang jelas antara networking, matchmaking, room management, simulasi, dan rendering memudahkan pemeliharaan dan pengembangan lebih lanjut.

### Kelebihan Implementasi

- **Pengelolaan Koneksi Robust** — Disconnection handling yang lengkap: pemain yang terputus otomatis dikeluarkan dari antrian matchmaking dan room.
- **Rate Limiting** — Perlindungan terhadap spam pesan menggunakan sliding-window algorithm.
- **Graceful Shutdown** — Server dapat dihentikan dengan Ctrl+C dan semua room akan di-cleanup dengan benar.
- **Scene-based Client Architecture** — Pemisahan logika per layar membuat kode client mudah dipahami dan diperluas.
- **Frustum Culling** — Optimasi rendering dengan melewati objek yang tidak terlihat di viewport kamera.
- **Server Publik** — Server telah di-deploy pada VPS (`168.144.139.241:8765`) sehingga dapat langsung digunakan tanpa konfigurasi server lokal.

### Pengembangan Lanjutan yang Memungkinkan

| Area             | Pengembangan yang Memungkinkan                                              |
|------------------|-----------------------------------------------------------------------------|
| Keamanan         | Autentikasi pemain, enkripsi WSS (TLS), validasi input yang lebih ketat    |
| Persistensi      | Database untuk menyimpan leaderboard global dan statistik pemain            |
| Skalabilitas     | Horizontal scaling dengan load balancer dan room server terpisah            |
| Gameplay         | Power-up, speed boost, skin ular, obstacle dinamis di arena                |
| Networking       | Delta compression untuk snapshot (hanya kirim perubahan, bukan full state)  |
| Anti-Cheat       | Server-side validation yang lebih ketat untuk input arah                    |
| Deployment       | Containerisasi dengan Docker, konfigurasi otomatis via environment variable |
| Observabilitas   | Metrics server (jumlah room aktif, rata-rata pemain, dll.) via Prometheus   |

---

*Proyek ini dikembangkan sebagai Final Project mata kuliah Pemrograman Jaringan.*
