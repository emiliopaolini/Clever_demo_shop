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
import numpy as np
import datetime
from locust import FastHttpUser, TaskSet, between
from faker import Faker

fake = Faker()

# Define your products and endpoint functions as before
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
    l.client.post("/setCurrency", {'currency_code': random.choice(currencies)})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products))

def viewCart(l):
    l.client.get("/cart")

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product)
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.randint(1,10)
    })

def empty_cart(l):
    l.client.post('/cart/empty')

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year + 1
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


# Custom wait time function that simulates a diurnal load with randomness
def diurnal_wait_time():
    # Current time in minutes since midnight (with seconds fraction)
    now = datetime.datetime.now()
    current_minute = now.hour * 60 + now.minute + now.second / 60.0
    
    # Compute minutes of day (mod 1440, though current_minute is already in [0,1440))
    minutes_of_day = current_minute % 1440

    # Generate slight random shifts for each peak (in minutes)
    shift1 = random.uniform(-10, 10)  # for the first peak (around noon)
    shift2 = random.uniform(-10, 10)  # for the second peak (around 18:00)
    
    # Calculate the two Gaussian peaks
    peak1 = np.exp(-((minutes_of_day - (720 + shift1)) ** 2) / (2 * 120 ** 2))
    peak2 = 0.5 * np.exp(-((minutes_of_day - (1080 + shift2)) ** 2) / (2 * 120 ** 2))
    
    # Add base rate, scaled peaks, and random noise in the range [-5, 5]
    rate = 50 + 30 * (peak1 + peak2) + (random.random() * 10 - 5)
    
    # Ensure rate is non-negative and then calculate delay in seconds.
    # Rate is in calls per minute, so delay = 60 / rate.
    if rate <= 0:
        return 60  # fallback delay if something goes wrong
    return 60 / rate

class UserBehavior(TaskSet):
    def on_start(self):
        index(self)

    tasks = {
        index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1
    }

class WebsiteUser(FastHttpUser):
    tasks = [UserBehavior]
    # Override the wait_time function to use the diurnal wait time
    wait_time = diurnal_wait_time