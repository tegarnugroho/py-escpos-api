from escpos import BluetoothConnection
from escpos.impl.epson import GenericESCPOS, CashDrawerException
from escpos import USBConnection


from flask import Blueprint, jsonify, request
from escpos import printer, exceptions as printer_exceptions, constants

app_routes = Blueprint('printer', __name__)


# API route to print a receipt and kick the cash drawer
@app_routes.route('printer/print-receipt', methods=['POST'])
def print_receipt():
    # Retrieve the receipt data from the request
    receipt_data = request.json.get('receipt_data')
    address = request.json.get('address')
    interface = request.json.get('interface')

    try:
        # Connect to the printer    
        printer = connect_to_printer()
        if (interface == 'USB') : printer = connect_to_bluetooth_printer(address=address)
        
        # Init the printer
        printer.init()
        
        # Set Header of the receipt
        printer.text_center('\n***** das POS-Unternehmen *****\n\n')
        printer.text_center('Beleg-Nr. 10052/013/0001   31.08.2022 11:33:37\n')
        printer.text_center('Frau Tamara (Cashier) served you at Station 1\n')
        
        # Set Footer of the receipt
        printer.text('\n')
        printer.ean13("123456")
        printer.text('\n\n\n***** Thank you for your purchase *****\n')
        printer.text('www.aks-anker.de/')
        
        # Cut the paper
        printer.cut()
        
        # Kick the cash drawer
        printer.kick_drawer(port=2)

        return jsonify({
            'message': 'Receipt printed and cash drawer kicked successfully!',
            'status_code': 200
        }), 200

    except printer_exceptions.Error as e:
        return jsonify({
            'message': f'Printing failed: {str(e)}',
            'status_code': 500,
            }), 500


def connect_to_bluetooth_printer(address):
    # uses SPD (service port discovery) services to find which port to connect to
    conn = BluetoothConnection.create(address)
    printer = GenericESCPOS(conn)
    
    return printer


def connect_to_printer(address):    
    # uses SPD (service port discovery) services to find which port to connect to
    conn = USBConnection.create('04b8:0e20,interface=0,ep_out=3,ep_in=0')
    printer = GenericESCPOS(conn)
    
    return printer
        

@app_routes.route('/printer/kick-cashdrawer', methods=['GET'])
def kick_cash_drawer():
    # Retrieve the bluetooth address from the request
    address = request.json.get('address')
    interface = request.json.get('interface')
    # Send command to open the cash drawer (specific to your printer model)
    # Replace the following line with the appropriate command for your printer
    try:
        printer = connect_to_printer()
        if (interface == 'USB') : printer = connect_to_bluetooth_printer(address=address)
        
        printer.init()
        printer.kick_drawer(port=2)
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
