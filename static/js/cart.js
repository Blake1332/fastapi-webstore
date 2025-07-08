//This is used to add items to the cart. Its just client side visualzation so it cant be trusted to be used in checkouts.
function addToCart(button) {
    const productId = button.dataset.productId;
    const productName = button.dataset.productName;
    const price = parseInt(button.dataset.productPrice);
    
    // Get existing cart from localStorage
    let cart = JSON.parse(localStorage.getItem('cart') || '{}');
    
    // Add/update product in cart
    if (cart[productId]) {
        cart[productId].quantity += 1;
    } else {
        cart[productId] = {
            name: productName,
            price: price,
            quantity: 1
        };
    }
    
    // Save cart
    localStorage.setItem('cart', JSON.stringify(cart));
    document.cookie = `cart=${JSON.stringify(cart)}; path=/`;
    alert('Item added to cart!');
    
    // Update cart count if the element exists
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems > 0 ? `(${totalItems})` : '';
    }
} 