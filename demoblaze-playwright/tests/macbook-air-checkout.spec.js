const { test, expect } = require('@playwright/test');
const { HomePage } = require('../pages/HomePage');
const { ProductPage } = require('../pages/ProductPage');
const { CartPage } = require('../pages/CartPage');

const MACBOOK_AIR = /MacBook air/i;

test.describe('Demoblaze laptop purchase flow', () => {
  test('MacBook Air can be added to cart and Place Order form is shown', async ({ page }) => {
    const homePage = new HomePage(page);
    const productPage = new ProductPage(page);
    const cartPage = new CartPage(page);

    await homePage.open();
    await homePage.goToLaptopsCategory();
    await homePage.openProduct(MACBOOK_AIR);

    await productPage.expectProductDisplayed(MACBOOK_AIR);
    await productPage.addToCart();
    await productPage.openCart();

    await cartPage.expectProductInCart(MACBOOK_AIR);
    await cartPage.expectProductHasPrice(MACBOOK_AIR);
    await cartPage.expectCartTotalDisplayed();

    await cartPage.openPlaceOrderForm();
    await cartPage.expectPlaceOrderFormVisible();
    await cartPage.expectCheckoutFieldsVisible();

    await expect(cartPage.checkoutFields.name).toBeEditable();
    await expect(cartPage.checkoutFields.country).toBeEditable();
    await expect(cartPage.checkoutFields.city).toBeEditable();
    await expect(cartPage.checkoutFields.creditCard).toBeEditable();
    await expect(cartPage.checkoutFields.month).toBeEditable();
    await expect(cartPage.checkoutFields.year).toBeEditable();
  });
});
