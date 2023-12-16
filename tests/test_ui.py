import logging

import allure
import requests
import json
from allure_commons._allure import step
from allure_commons.types import AttachmentType
from selene import browser
from selene.support.conditions import have
from requests import Response

LOGIN = "i@i.io"
PASSWORD = "qaz@321"
WEB_URL = "https://demowebshop.tricentis.com/"
API_URL = "https://demowebshop.tricentis.com/"


def response_logging(response: Response):
    logging.info("Request: " + response.request.url)
    if response.request.body:
        logging.info("INFO Request body: " + response.request.body)
    logging.info("Request headers: " + str(response.request.headers))
    logging.info("Response code " + str(response.status_code))
    logging.info("Response: " + response.text)


def logout():
    with allure.step("Выход из сессии"):
        browser.open(WEB_URL + "/logout").wait_until(have.title("Demo Web Shop"))


def response_attaching(response: Response):
    allure.attach(
        body=response.request.url,
        name="Request url",
        attachment_type=AttachmentType.TEXT,
    )
    allure.attach(
        body=json.dumps(response.request.body, indent=4, ensure_ascii=True),
        name="Request body",
        attachment_type=AttachmentType.JSON,
        extension="json",
    )
    if response.status_code != 302:
        allure.attach(
            body=json.dumps(response.json(), indent=4, ensure_ascii=True),
            name="Response",
            attachment_type=AttachmentType.JSON,
            extension="json",
        )


def get_history_cookie(url, **kwargs):
    with allure.step("Получение куки"):
        response: Response = requests.post(url, **kwargs)

        response_attaching(response)
        response_logging(response)

        return response.cookies.get("Nop.customer")


def open_cart_with_history(cookie):
    with allure.step("Инициализация браузера"):
        browser.open(WEB_URL).wait_until(have.title("Demo Web Shop"))
        browser.driver.add_cookie({"name": "Nop.customer", "value": cookie})
        # browser.config.timeout = 10
        browser.open(WEB_URL + "/cart").wait_until(
            have.title("Demo Web Shop. Shopping Cart")
        )


def test_login():
    """Successful authorization to some demowebshop (UI)"""
    with step("Open login page"):
        browser.open(WEB_URL + "login")

    with step("Fill login form"):
        browser.element("#Email").send_keys(LOGIN)
        browser.element("#Password").send_keys(PASSWORD).press_enter()

    with step("Verify successful authorization"):
        browser.element(".account").should(have.text(LOGIN))
        logout()


def test_login_though_api():
    """Successful authorization to some demowebshop (API)"""
    with step("Login with API"):
        response: Response = requests.post(
            url=API_URL + "/login",
            data={"Email": LOGIN, "Password": PASSWORD, "RememberMe": False},
            allow_redirects=False,
        )
        response_attaching(response)
        response_logging(response)
    with step("Get cookie from API"):
        cookie = response.cookies.get("NOPCOMMERCE.AUTH")

    with step("Set cookie from API"):
        browser.open(WEB_URL)
        browser.driver.add_cookie({"name": "NOPCOMMERCE.AUTH", "value": cookie})
        browser.open(WEB_URL)

    with step("Verify successful authorization"):
        browser.element(".account").should(have.text(LOGIN))
        logout()

def test_smartphone_adding():
    with step("Test precondition: cart filling"):
        cookie = get_history_cookie(WEB_URL + "/addproducttocart/details/43/1")

    with step("Set cookie from API"):
        open_cart_with_history(cookie)

    with step("Check results"):
        browser.all('[class="cart-item-row"]').element_by(
            have.text("Smartphone")
        ).element('[class="qty-input"]').should(have.value("1"))
        browser.all('[class="cart-item-row"]').element_by(
            have.text("Smartphone")
        ).element('[class="product-unit-price"]').should(have.text("100.00"))
        browser.element('[class="product-price order-total"]').should(
            have.text("100.00")
        )


def test_book_adding():
    with step("Test precondition: cart filling"):
        cookie = get_history_cookie(WEB_URL + "/addproducttocart/catalog/13/1/1")

    with step("Set cookie from API"):
        open_cart_with_history(cookie)

    with step("Check results"):
        browser.all('[class="cart-item-row"]').element_by(
            have.text("Computing and Internet")
        ).element('[class="qty-input"]').should(have.value("1"))
        browser.all('[class="cart-item-row"]').element_by(
            have.text("Computing and Internet")
        ).element('[class="product-unit-price"]').should(have.text("10.00"))
        browser.element('[class="product-price order-total"]').should(
            have.text("10.00")
        )
