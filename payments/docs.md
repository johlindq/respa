# Payments

## API

- Checking available products (ATM rents) for resources

    Resources have `products` field that contains a list of the resource's products.

    Example response (GET `/v1/resource/`):

    ```json
    ...

    "products": [
        {
            "id": "awevmfmr3w5a",
            "type": "rent",
            "name": {
                "fi": "testivuokra",
                "en": "test rent"
            },
            "description": {
                "fi": "Testivuokran kuvaus.",
                "en": "Test rent description."
            },
            "tax_percentage": "24.00",
            "price": "12.40",
            "price_type": "per_hour"
        }
    ],

    ...
    ```

    At least for now, when there is a `rent` type product available, and there should be only one of those at a time, it should be ordered and paid in order to create a successful reservation.

    Currently `rent` is the only `type` option, but there will be new ones in the future.

    Currently `per_hour` is the only `price_type` option, but there will be new ones in the future.

- Creating an order

    Order endpoint is used to create an order of product(s).

    Example request (POST `/v1/order/`):

    ```json
    {
        "reservation": 191999,
        "order_lines": [
            {
                "product": "awemfcd2iqlq",
                "quantity": 1
            }
        ],
        "payer_first_name": "Ville",
        "payer_last_name": "Virtanen",
        "payer_email_address": "ville@virtanen.com",
        "payer_address_street": "Virtatie 5",
        "payer_address_zip": "55555",
        "payer_address_city": "Virtala",
        "return_url": "https://varaamo.hel.fi/payment-return-url/"
    }
    ```

    `return_url` is the URL where the user's browser will be redirected after the payment process. Typically it should be some kind of "payment done" view in the UI.

    `quantity` can be omitted when it is 1 (and for rents it probably should always be).

    Example response:

    ```json
    {
        "id": 59,
        "order_lines": [
            {
                "product": {
                    "id": "awemfcd2iqlq",
                    "type": "rent",
                    "name": {
                        "fi": "testivuokra"
                    },
                    "description": {
                        "fi": "testikuvaus"
                    },
                    "tax_percentage": "24.00",
                    "price": "12.40",
                    "price_type": "per_hour"
                },
                "quantity": 1,
                "price": "18.60"
            }
        ],
        "price": "18.60",
        "payment_url": "https://payform.bambora.com/pbwapi/token/d02317692040937087a4c04c303dd0da14441f6f492346e40cea8e6a6c7ffc7c",
        "status": "waiting",
        "order_number": "awemfcd2icdcd",
        "payer_first_name": "Ville",
        "payer_last_name": "Virtanen",
        "payer_email_address": "ville@virtanen.com",
        "payer_address_street": "Virtatie 5",
        "payer_address_zip": "55555",
        "payer_address_city": "Virtala",
        "reservation": 191999
    }
    ```

    After a successful order creation, the UI should redirect the user to the URL in `payment_url` in order to start a payment process. Once the payment has been carried out, the user is redirected to the return url given when creating the order. The return url will also contain query params `payment_status=<success or failure>` and `order_id=<ID of the order in question>`.

    Example full return url: `https://varaamo.hel.fi/payment-return-url/?payment_status=success&order_id=59`

- Checking prices of orders

    Price checking endpoint can be used to check the price of an order without actually creating the order.

    Example request (POST `/v1/order/check_price/`):

    ```json
    {
        "begin": "2019-04-11T08:00:00+03:00",
        "end": "2019-04-11T11:00:00+03:00",
        "order_lines": [
            {
                "product": "awemfcd2iqlq",
                "quantity": 5
            }
        ]
    }
    ```

    Example response:

    ```json
    {
        "order_lines": [
            {
                "product": {
                    "id": "awemfcd2iqlq",
                    "type": "rent",
                    "name": {
                        "fi": "testivuokra"
                    },
                    "description": {
                        "fi": "testikuvaus"
                    },
                    "tax_percentage": "24.00",
                    "price": "12.40",
                    "price_type": "per_hour"
                },
                "quantity": 5,
                "price": "186.00"
            }
        ],
        "price": "186.00",
        "begin": "2019-04-11T08:00:00+03:00",
        "end": "2019-04-11T11:00:00+03:00"
    }
    ```

- Order data in reservation API endpoint

    Order data is also available in the `reservation` API endpoint in `orders` field. The field is present only on reservations for which the current user has permission to view orders (either own reservation or via the explicit view order permission).

    Example response (GET `/v1/reservation/`):

    ```json
    ...

    "orders": [67],

    ...
    ```

    Typically the orders field contains only IDs of the orders. It is also possible to request for the whole order data by adding query param `include=orders` to the request.

    Example response (GET `/v1/reservation/?include=orders`):

    ```json
    ...

    "orders": [
        {
            "id": 67,
            "status": "waiting",
            "order_number": "da7e806f-1f7b-4683-a6cb-a844748b7447",
            "payer_first_name": "Ville",
            "payer_last_name": "Virtanen",
            "payer_email_address": "ville@virtanen.com",
            "payer_address_street": "Virtatie 5",
            "payer_address_zip": "55555",
            "payer_address_city": "Virtala",
            "price": "17.10",
            "order_lines": [
                {
                    "product": {
                        "id": "awemfcd2iqlq",
                        "type": "rent",
                        "name": {
                            "fi": "testivuokra"
                        },
                        "description": {
                            "fi": "testikuvaus"
                        },
                        "tax_percentage": "14.00",
                        "price": "11.40",
                        "price_type": "per_hour"
                    },
                    "quantity": 1,
                    "price": "17.10"
                }
            ]
        }
    ],

    ...
    ```