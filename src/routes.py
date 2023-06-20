from escpos import BluetoothConnection
from escpos.impl.epson import GenericESCPOS, CashDrawerException
from escpos import USBConnection


from flask import Blueprint, jsonify, request

app_routes = Blueprint('printer', __name__)


# API route to print a receipt and kick the cash drawer
@app_routes.route('printer/print-receipt', methods=['POST'])
def print_receipt():
    # Retrieve the parameters from the request
    receipt_data = request.json.get('receipt_data')
    address = request.json.get('address')
    interface = request.json.get('interface')

    try:
        # Connect to the printer    
        printer = connect_to_printer()
        
        # Init the printer
        printer.init()
        
        # Set Header of the receipt
        printer.text_center('\n***** das POS-Unternehmen *****\n\n')
        printer.text_center('Beleg-Nr. 10052/013/0001   31.08.2022 11:33:37\n')
        printer.text_center('Frau Tamara (Cashier) served you at Station 1\n')
        
        # Set the items sections
        for index, item in enumerate(receipt_data['items'], start=1):
            number = str(index)
            name = item['name']
            product_id = item['product_id']
            quantity = item['quantity']
            price = f"{item['price']:.2f}"
            total = f"{item['price'] * item['quantity']:.2f}"
            
            printer.text(f"{number} {name}\n {product_id} {quantity} {price} {total}")
        
        # Set Footer of the receipt
        printer.text('\n')
        printer.ean13("1234567891011")
        printer.text('\n\n\n***** Thank you for your purchase *****\n')
        printer.text('www.aks-anker.de/')    
        
        printer.lf()
        
        # Cut the paper
        printer.cut(feed=255)

        return jsonify({
            'message': 'Receipt printed and cash drawer kicked successfully!',
            'status_code': 200
        }), 200

    except Exception as e:
        return jsonify({
            'message': f'Printing failed: {str(e)}',
            'status_code': 500,
            }), 500


def connect_to_bluetooth_printer(address):
    # BluetoothConnection
    conn = BluetoothConnection.create(address)
    printer = GenericESCPOS(conn)
    
    return printer


def connect_to_printer():    
    # USBConnection
    conn = USBConnection.create('04b8:0e20,interface=0,ep_out=3,ep_in=0')
    printer = GenericESCPOS(conn)
    
    return printer
        

@app_routes.route('/printer/kick-cashdrawer', methods=['GET'])
def kick_cash_drawer():
    # Retrieve the parameters from the request
    address = request.json.get('address')
    interface = request.json.get('interface')
    
    try:
        printer = connect_to_printer()
        if (interface == 'USB') : printer = connect_to_bluetooth_printer(address=address)
        
        # Init the printer        
        printer.init()
        
        # Kick the cash drawer      
        printer.kick_drawer(port=0)
        return jsonify({
            'message': 'Cash drawer kicked successfully!',
            'status_code': 200
        }), 200
    except CashDrawerException as e:
        # Log or handle the error appropriately
        return jsonify({
            'message': f'Failed to kick the cash drawer: {str(e)}',
            'status_code': 500,
            }), 500
