"""
VendStack ShipStation API Client
- Fetch shipping rates
- Purchase labels
- Get label PDF for printing
"""

import json
import base64
import urllib.request
import urllib.error

SHIPSTATION_BASE = 'https://ssapi.shipstation.com'


class ShipStationClient:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret

    def _auth_header(self):
        if not self.api_key or not self.api_secret:
            return None
        credentials = base64.b64encode(
            f'{self.api_key}:{self.api_secret}'.encode()
        ).decode()
        return f'Basic {credentials}'

    def _request(self, method, path, data=None):
        auth = self._auth_header()
        if not auth:
            return {'error': 'ShipStation API credentials not configured'}

        url = f'{SHIPSTATION_BASE}{path}'
        body = json.dumps(data).encode('utf-8') if data else None

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header('Authorization', auth)
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            return {'error': f'ShipStation API error {e.code}', 'details': error_body}
        except Exception as e:
            return {'error': str(e)}

    def fetch_rates(self, order_data):
        """
        Fetch shipping rates from ShipStation.
        order_data should include: carrierCode, fromPostalCode, toPostalCode,
        toCountry, weight {value, units}, dimensions (optional)
        """
        return self._request('POST', '/shipments/getrates', order_data)

    def fetch_rates_for_order(self, order):
        """Fetch rates for an internal order dict. Returns list of rate options."""
        # Parse address for postal code
        address = order.get('address', '')
        postal_code = ''
        if address:
            # Try to extract UK postcode
            import re
            match = re.search(r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}', address.upper())
            if match:
                postal_code = match.group()

        items = json.loads(order.get('items_json', '[]')) if isinstance(order.get('items_json'), str) else order.get('items_json', [])
        total_weight = sum(item.get('weight', 0.5) for item in items) if items else 1.0

        # Fetch rates from multiple carriers
        carriers = ['royal_mail', 'stamps_com', 'fedex', 'ups']
        all_rates = []

        for carrier in carriers:
            rate_request = {
                'carrierCode': carrier,
                'fromPostalCode': 'SW1A 1AA',  # Default UK origin
                'toPostalCode': postal_code or 'EC1A 1BB',
                'toCountry': 'GB',
                'weight': {
                    'value': total_weight,
                    'units': 'kilograms',
                },
                'confirmation': 'none',
                'residential': True,
            }
            result = self._request('POST', '/shipments/getrates', rate_request)
            if isinstance(result, list):
                all_rates.extend(result)
            elif isinstance(result, dict) and not result.get('error'):
                all_rates.append(result)

        return all_rates

    def purchase_label(self, label_data):
        """
        Purchase a shipping label.
        label_data should include: carrierCode, serviceCode, fromPostalCode,
        toPostalCode, toCountry, weight, etc.
        """
        return self._request('POST', '/shipments/createlabel', label_data)

    def purchase_label_for_order(self, order, carrier_code, service_code):
        """Purchase a label for an internal order. Returns label info."""
        address = order.get('address', '')
        postal_code = ''
        if address:
            import re
            match = re.search(r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}', address.upper())
            if match:
                postal_code = match.group()

        items = json.loads(order.get('items_json', '[]')) if isinstance(order.get('items_json'), str) else order.get('items_json', [])
        total_weight = sum(item.get('weight', 0.5) for item in items) if items else 1.0

        label_data = {
            'carrierCode': carrier_code,
            'serviceCode': service_code,
            'packageCode': 'package',
            'confirmation': 'none',
            'shipDate': order.get('order_date', '2024-01-01'),
            'weight': {
                'value': total_weight,
                'units': 'kilograms',
            },
            'shipFrom': {
                'name': 'VendStack Seller',
                'street1': '1 Commerce Street',
                'city': 'London',
                'postalCode': 'SW1A 1AA',
                'country': 'GB',
            },
            'shipTo': {
                'name': order.get('customer_name', ''),
                'street1': address.split(',')[0] if address else '',
                'city': address.split(',')[1].strip() if address and ',' in address else 'London',
                'postalCode': postal_code or 'EC1A 1BB',
                'country': 'GB',
            },
            'testLabel': True,
        }

        return self._request('POST', '/shipments/createlabel', label_data)

    def get_label_pdf(self, shipment_id):
        """Get label PDF URL for a shipment."""
        return self._request('GET', f'/shipments/{shipment_id}')

    def void_label(self, shipment_id):
        """Void a shipping label."""
        return self._request('PUT', '/shipments/voidlabel', {'shipmentId': shipment_id})


# Demo rates for when ShipStation creds aren't configured
DEMO_RATES = [
    {
        'serviceName': 'Royal Mail Tracked 24',
        'serviceCode': 'rm_tracked_24',
        'carrierCode': 'royal_mail',
        'shipmentCost': 3.95,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 1,
    },
    {
        'serviceName': 'Royal Mail Tracked 48',
        'serviceCode': 'rm_tracked_48',
        'carrierCode': 'royal_mail',
        'shipmentCost': 2.85,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 3,
    },
    {
        'serviceName': 'DPD Next Day',
        'serviceCode': 'dpd_next_day',
        'carrierCode': 'dpd',
        'shipmentCost': 6.50,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 1,
    },
    {
        'serviceName': 'Evri Standard',
        'serviceCode': 'hermes_standard',
        'carrierCode': 'hermes',
        'shipmentCost': 2.49,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 5,
    },
    {
        'serviceName': 'UPS Standard',
        'serviceCode': 'ups_standard',
        'carrierCode': 'ups',
        'shipmentCost': 7.99,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 2,
    },
    {
        'serviceName': 'FedEx Economy',
        'serviceCode': 'fedex_economy',
        'carrierCode': 'fedex',
        'shipmentCost': 8.50,
        'otherCost': 0,
        'currency': 'GBP',
        'estimatedDays': 3,
    },
]
