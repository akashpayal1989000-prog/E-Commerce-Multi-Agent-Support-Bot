# data/policies.py

POLICIES = {
    "return": """
        Return Policy:
        - Smartphones & Electronics: 10 days from delivery date
        - Footwear & Clothing: 7 days from delivery date
        - Kitchen Appliances: 10 days from delivery date
        - Ethnic Wear (Sarees, Kurtas): No returns accepted
        - Item must be unused and in original packaging
        - All tags and accessories must be intact
    """,

    "refund": """
        Refund Policy:
        - UPI & Card payments: Refund in 5-7 business days
        - COD orders: Refund via bank transfer in 7-10 business days
        - Cancelled orders: Refund within 3-5 business days
        - Damaged product: Immediate refund or replacement
        - Razorpay payment ID required for refund tracking
    """,

    "shipping": """
        Shipping Policy:
        - Free shipping on orders above Rs 499
        - Standard delivery: 3-5 working days
        - Express delivery: 1-2 working days (Rs 99 extra)
        - Couriers used: Delhivery, BlueDart, Ekart
        - Orders placed before 2 PM shipped same day
        - Tracking available via AWB number
    """,

    "cancellation": """
        Cancellation Policy:
        - Orders can be cancelled before shipping for free
        - Once shipped, cancellation is not possible
        - After delivery, initiate return within policy window
        - Cancelled order refunds processed in 3-5 business days
    """
}