import random, time
import psycopg2

conn = psycopg2.connect(host="localhost", port=5432, user="upi",
                        password="upi", dbname="upidb")
conn.autocommit = True
cur = conn.cursor()

CITIES = ["Hyderabad", "Mumbai", "Delhi", "Chennai", "Bengaluru"]
MERCHANTS = ["Swiggy", "Zomato", "Amazon", "BigBasket", "IRCTC", "Uber", "Local Store"]
N_USERS = 20

def seed():
    cur.execute("SELECT count(*) FROM users")
    if cur.fetchone()[0] == 0:
        for i in range(1, N_USERS + 1):
            cur.execute("INSERT INTO users (name, city) VALUES (%s, %s)",
                        (f"user{i}", CITIES[i % len(CITIES)]))
            cur.execute("INSERT INTO devices (device_id, user_id) VALUES (%s, %s)",
                        (f"dev-u{i}", i))

def txn(user, device, amount):
    cur.execute(
        "INSERT INTO transactions (user_id, device_id, amount, merchant, city) "
        "VALUES (%s, %s, %s, %s, %s)",
        (user, device, round(amount, 2), random.choice(MERCHANTS),
         CITIES[user % len(CITIES)]))

def normal():
    u = random.randint(1, N_USERS)
    txn(u, f"dev-u{u}", random.uniform(20, 2000))
    print(f"normal  user={u}")

def burst():
    u = random.randint(1, N_USERS)
    for _ in range(8):
        txn(u, f"dev-u{u}", random.uniform(100, 900))
        time.sleep(0.3)
    print(f"FRAUD burst user={u}")

def huge():
    u = random.randint(1, N_USERS)
    txn(u, f"dev-u{u}", random.uniform(50000, 200000))
    print(f"FRAUD huge amount user={u}")

def new_device():
    u = random.randint(1, N_USERS)
    txn(u, f"dev-new-{random.randint(1000, 9999)}", random.uniform(20000, 80000))
    print(f"FRAUD new device user={u}")

seed()
print("Generating... press Ctrl+C to stop")
while True:
    r = random.random()
    if r < 0.05: burst()
    elif r < 0.08: huge()
    elif r < 0.11: new_device()
    else: normal()
    time.sleep(1)