"""
VendStack AI Messaging Engine
- Intent detection (rule-based)
- Sentiment analysis (rule-based)
- Rule-based reply generation
- GPT-4 fallback when OPENAI_API_KEY is set
"""

import re
import json
import os

# --- Intent Detection ---

INTENT_PATTERNS = {
    'where_is_my_order': [
        r'where\s+(is|are)\s+(my|the)\s+order',
        r'track(ing)?\s*(number|info|update|status)',
        r'when\s+(will|does)\s+(it|my order)\s+(arrive|ship|deliver)',
        r'order\s+status',
        r'hasn\'?t\s+(arrived|shipped|been delivered)',
        r'not\s+(received|arrived|delivered)',
        r'delivery\s+(date|time|update|status)',
        r'dispatch(ed)?',
        r'shipping\s+update',
    ],
    'wrong_item': [
        r'wrong\s+(item|product|order|thing|colour|color|size)',
        r'received\s+(the\s+)?wrong',
        r'sent\s+(me\s+)?(the\s+)?wrong',
        r'not\s+what\s+i\s+ordered',
        r'incorrect\s+(item|product|order)',
        r'different\s+(item|product|than)',
        r'mix(ed)?\s*up',
    ],
    'refund_request': [
        r'refund',
        r'money\s+back',
        r'return(ing)?\s+(the|this|my)',
        r'cancel(lation)?(\s+of)?\s+(my\s+)?order',
        r'want\s+(my\s+)?money\s+back',
        r'full\s+refund',
        r'partial\s+refund',
        r'reimburse',
    ],
    'product_question': [
        r'does\s+(this|it)\s+come\s+(in|with)',
        r'what\s+(size|colour|color|material|weight|dimensions)',
        r'is\s+(this|it)\s+(compatible|suitable|available)',
        r'how\s+(big|heavy|tall|wide|long)\s+is',
        r'can\s+(i|you)\s+(use|tell|confirm)',
        r'product\s+(info|information|details|specs|question)',
        r'stock\s+(availability|available|level)',
        r'do\s+you\s+(have|sell|stock|carry)',
    ],
}

def detect_intent(text):
    """Detect message intent from text. Returns intent string."""
    text_lower = text.lower().strip()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent
    return 'general'


# --- Sentiment Analysis ---

POSITIVE_WORDS = {
    'thank', 'thanks', 'great', 'excellent', 'amazing', 'wonderful', 'perfect',
    'love', 'happy', 'pleased', 'satisfied', 'brilliant', 'fantastic', 'awesome',
    'appreciate', 'helpful', 'good', 'best', 'lovely', 'superb', 'glad',
}

NEGATIVE_WORDS = {
    'terrible', 'awful', 'horrible', 'worst', 'disgusting', 'angry', 'furious',
    'disappointed', 'unacceptable', 'poor', 'rubbish', 'useless', 'pathetic',
    'scam', 'fraud', 'complaint', 'disgrace', 'outraged', 'appalling',
    'never', 'hate', 'broken', 'damaged', 'faulty', 'defective', 'rip off',
    'waste', 'ridiculous', 'incompetent', 'abysmal',
}

def detect_sentiment(text):
    """Simple word-based sentiment detection. Returns positive/negative/neutral."""
    words = set(re.findall(r'\w+', text.lower()))
    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)

    if neg_count > pos_count:
        return 'negative'
    elif pos_count > neg_count:
        return 'positive'
    return 'neutral'


# --- Rule-Based Reply Templates ---

REPLY_TEMPLATES = {
    'where_is_my_order': {
        'professional': (
            "Thank you for your enquiry regarding your order {order_number}. "
            "Your order is currently {status}. "
            "{tracking_info}"
            "If you have any further questions, please don't hesitate to reach out."
        ),
        'friendly': (
            "Hi {customer_name}! 👋 Thanks for getting in touch about your order {order_number}. "
            "Good news — your order is currently {status}. "
            "{tracking_info}"
            "Let me know if there's anything else I can help with!"
        ),
        'empathetic': (
            "I completely understand your concern about your order {order_number}, {customer_name}. "
            "Waiting for a delivery can be stressful. Your order is currently {status}. "
            "{tracking_info}"
            "I'm here if you need anything else at all."
        ),
        'firm': (
            "Regarding order {order_number}: the current status is {status}. "
            "{tracking_info}"
            "Standard delivery timescales apply as stated at point of purchase."
        ),
    },
    'wrong_item': {
        'professional': (
            "I'm sorry to hear you've received the wrong item with order {order_number}. "
            "We take this matter seriously and would like to resolve it immediately. "
            "Please could you send a photo of the item received? We'll arrange for the correct item "
            "to be sent out straight away, along with a prepaid return label for the incorrect item."
        ),
        'friendly': (
            "Oh no, I'm so sorry about that mix-up with your order {order_number}! 😟 "
            "That's definitely not the experience we want you to have. "
            "Could you pop a quick photo over of what you received? "
            "We'll get the right item out to you ASAP and sort a free return for the wrong one!"
        ),
        'empathetic': (
            "I'm truly sorry about this error with order {order_number}, {customer_name}. "
            "I can only imagine how frustrating it must be to receive the wrong item. "
            "This is entirely our fault and I want to make it right. "
            "If you could share a photo of what arrived, I'll personally ensure the correct item "
            "is dispatched to you as a priority, with a prepaid return label enclosed."
        ),
        'firm': (
            "We acknowledge the incorrect item was sent for order {order_number}. "
            "To process the exchange, please provide a photograph of the item received. "
            "A replacement will be dispatched upon confirmation, along with a prepaid return label."
        ),
    },
    'refund_request': {
        'professional': (
            "Thank you for contacting us regarding a refund for order {order_number}. "
            "We've reviewed your request and would like to process this for you. "
            "The refund of {total} will be issued to your original payment method "
            "within 3-5 business days. You'll receive a confirmation email shortly."
        ),
        'friendly': (
            "Hi {customer_name}! Thanks for reaching out about your order {order_number}. "
            "No worries at all — I've started the refund process for you. "
            "You should see {total} back in your account within 3-5 business days. "
            "I'll send you a confirmation email too. Sorry for any hassle! 🙏"
        ),
        'empathetic': (
            "I understand your frustration, {customer_name}, and I'm sorry that order {order_number} "
            "didn't meet your expectations. Your satisfaction means a lot to us. "
            "I'm processing a refund of {total} right away — it should appear in your account "
            "within 3-5 business days. Please don't hesitate to reach out if you need anything else."
        ),
        'firm': (
            "Refund request acknowledged for order {order_number}. "
            "Amount of {total} will be returned to the original payment method "
            "within 3-5 business days, subject to our returns policy terms."
        ),
    },
    'product_question': {
        'professional': (
            "Thank you for your interest in our products. "
            "I'd be happy to help answer your question. "
            "Could you let me know exactly which product you're enquiring about "
            "so I can provide you with the most accurate information?"
        ),
        'friendly': (
            "Hey {customer_name}! Great question! 😊 "
            "I'd love to help you out with that. "
            "Could you let me know which specific product you're looking at? "
            "I'll get you all the details you need!"
        ),
        'empathetic': (
            "Thank you for reaching out, {customer_name}. It's great that you're taking the time "
            "to learn more before making a decision. I want to make sure you have all the "
            "information you need. Could you share which product you're interested in? "
            "I'll do my best to answer thoroughly."
        ),
        'firm': (
            "Please specify the product SKU or title for your enquiry. "
            "Product specifications are available on the listing page. "
            "For additional details not listed, provide the specific information required."
        ),
    },
    'general': {
        'professional': (
            "Thank you for contacting us, {customer_name}. "
            "I've received your message and will look into this for you. "
            "Please allow up to 24 hours for a full response. "
            "If your matter is urgent, please reply with 'URGENT' in the subject."
        ),
        'friendly': (
            "Hi {customer_name}! Thanks for getting in touch! 😊 "
            "I've got your message and I'm on it. "
            "I'll get back to you with a proper response as soon as I can — "
            "usually within 24 hours. Anything urgent, just let me know!"
        ),
        'empathetic': (
            "Thank you for reaching out, {customer_name}. "
            "I appreciate you taking the time to contact us. "
            "I want to make sure I give your message the attention it deserves, "
            "so please allow me up to 24 hours to provide a thorough response."
        ),
        'firm': (
            "Message received. A response will be provided within 24 hours. "
            "For order-specific enquiries, include your order number for faster processing."
        ),
    },
}


def generate_rule_reply(intent, tone, context=None):
    """Generate a rule-based reply for the given intent and tone."""
    context = context or {}
    tone = tone if tone in ('professional', 'friendly', 'empathetic', 'firm') else 'professional'

    template = REPLY_TEMPLATES.get(intent, REPLY_TEMPLATES['general']).get(tone, '')

    tracking_info = ''
    if context.get('tracking_number'):
        tracking_info = f"Your tracking number is {context['tracking_number']}. "
    elif intent == 'where_is_my_order':
        tracking_info = "We're preparing your order and tracking details will be sent once dispatched. "

    return template.format(
        customer_name=context.get('customer_name', 'there'),
        order_number=context.get('order_number', 'your order'),
        status=context.get('status', 'being processed'),
        total=context.get('total', 'the order amount'),
        tracking_info=tracking_info,
    )


# --- GPT-4 Fallback ---

def generate_gpt_reply(message_body, intent, sentiment, tone, context=None, api_key=None):
    """Generate a reply using GPT-4. Returns None if no API key or on failure."""
    if not api_key:
        return None

    try:
        import urllib.request
        import urllib.error

        context = context or {}
        system_prompt = (
            f"You are a customer service AI for a UK ecommerce seller. "
            f"Reply tone: {tone}. Detected intent: {intent}. Sentiment: {sentiment}. "
            f"Keep replies concise (2-4 sentences), warm, and helpful. "
            f"Use British English. Never make up order details. "
            f"Customer name: {context.get('customer_name', 'Customer')}. "
            f"Order number: {context.get('order_number', 'N/A')}."
        )

        payload = json.dumps({
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message_body},
            ],
            'max_tokens': 300,
            'temperature': 0.7,
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()

    except Exception:
        return None


def compose_message(body, tone='professional', context=None, api_key=None):
    """Full AI compose: free-form message with tone."""
    if api_key:
        reply = generate_gpt_reply(
            body, 'compose', 'neutral', tone, context, api_key
        )
        if reply:
            return reply

    # Fallback: echo back a polished version
    return (
        f"Thank you for your message. We have received your enquiry and "
        f"will respond within 24 hours with a detailed answer. "
        f"If your matter is urgent, please let us know."
    )


def generate_reply(message_body, tone='professional', context=None, api_key=None):
    """Main entry point: detect intent + sentiment, generate reply."""
    intent = detect_intent(message_body)
    sentiment = detect_sentiment(message_body)

    # Try GPT-4 first if key is available
    if api_key:
        gpt_reply = generate_gpt_reply(
            message_body, intent, sentiment, tone, context, api_key
        )
        if gpt_reply:
            return {
                'reply': gpt_reply,
                'intent': intent,
                'sentiment': sentiment,
                'source': 'gpt-4',
            }

    # Fall back to rule-based
    reply = generate_rule_reply(intent, tone, context)
    return {
        'reply': reply,
        'intent': intent,
        'sentiment': sentiment,
        'source': 'rule-based',
    }
