#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import math
from locust import FastHttpUser, TaskSet, between, LoadTestShape
from faker import Faker
import datetime
import csv
fake = Faker()

products = [
    '0PUK6V6EV0',
    '1YMWWN1N4O',
    '2ZYFJ3GM2N',
    '66VCHSJNUP',
    '6E92ZMYYFZ',
    '9SIQT8TOJO',
    'L9ECAV7KIM',
    'LS4PSXUNUM',
    'OLJCESPC7Z']

def index(l):
    l.client.get("/")

def setCurrency(l):
    currencies = ['EUR', 'USD', 'JPY', 'CAD', 'GBP', 'TRY']
    l.client.post("/setCurrency",
        {'currency_code': random.choice(currencies)})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products))

def viewCart(l):
    l.client.get("/cart")

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product)
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.randint(1,10)})
    
def empty_cart(l):
    l.client.post('/cart/empty')

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year+1
    l.client.post("/cart/checkout", {
        'email': fake.email(),
        'street_address': fake.street_address(),
        'zip_code': fake.zipcode(),
        'city': fake.city(),
        'state': fake.state_abbr(),
        'country': fake.country(),
        'credit_card_number': fake.credit_card_number(card_type="visa"),
        'credit_card_expiration_month': random.randint(1, 12),
        'credit_card_expiration_year': random.randint(current_year, current_year + 70),
        'credit_card_cvv': f"{random.randint(100, 999)}",
    })
    
def logout(l):
    l.client.get('/logout')  


class UserBehavior(TaskSet):

    def on_start(self):
        index(self)

    tasks = {index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1}

class WebsiteUser(FastHttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 10)

class DiurnalLoadShape(LoadTestShape):
    """
    A simple diurnal load shape with two daily peaks:
      - One peak around 12:00 (noon)
      - Another, smaller peak around 18:00 (6 p.m.)
    We add random shifts (±10 minutes) so that the peaks do not occur at exactly
    the same time each day, plus some noise for realism.
    """

    total_run_time = 86400
    results = []

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.total_run_time:
            fieldnames = ["run_time", "user_count"]
            with open("user_count.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.results:
                    writer.writerow(row)
            return None
        
        # scaled_run_time = run_time * 144

        current_minute = (run_time // 60) % 1440

        # shift_peak1 = random.uniform(-10, 10)
        # shift_peak2 = random.uniform(-10, 10)
        # you should add shift_peak to 720 and 1080 
        # respectively if you want to run this test over multiple days

        peak1 = math.exp(-((current_minute - 720)**2) / (2 * 120**2))
        peak2 = 0.5 * math.exp(-((current_minute - 1080)**2) / (2 * 120**2))

        noise = random.uniform(-5, 5)

        user_count = 50 + 250 * (peak1 + peak2) + noise

        if user_count < 0:
            user_count = 0

        user_count = int(user_count)
        spawn_rate = user_count

        self.results.append({"run_time": run_time, "user_count": user_count})

        return (user_count, spawn_rate)
