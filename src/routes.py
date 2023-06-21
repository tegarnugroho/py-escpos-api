import math

from datetime import datetime
from escpos import BluetoothConnection
from escpos.impl.epson import GenericESCPOS, CashDrawerException
from escpos import USBConnection, showcase
from flask import Blueprint, jsonify, request

app_routes = Blueprint('printer', __name__)

def _get_ruler(printer, char='-'):
    return char * printer.feature.columns.normal

def _build_item_mask(width, alignments=None, column_widths=None, gap=1):
    # <alignments> str, for example "<>^" (left, right, center)
    # <column_widths> list(float, ...)
    if len(alignments) != len(column_widths):
        raise ValueError('Alignment spec and number of columns must match')
    if sum(column_widths) > 100:
        raise ValueError('Sum of column widths must not be greater than 100%')
    width = width - (len(alignments) * gap) - gap
    columns = []
    for i, perc in enumerate(column_widths):
        col_len = int(math.ceil(perc * width))
        columns.append('{{:{:s}{:d}s}}'.format(alignments[i], col_len))
    return (' ' * gap).join(columns)


# API route to print a receipt and kick the cash drawer
@app_routes.route('printer/print-receipt', methods=['POST'])
def print_receipt():
    # Retrieve the parameters from the request
    receipt_data = request.json.get('receipt_data')
    address = request.json.get('address')
    interface = request.json.get('interface')

    try:
        # Connect to the printer    
        if (interface == 'USB'):
            printer = connect_to_printer()
        else:
            printer = connect_to_bluetooth_printer(address=address)
            
        ruler_single = _get_ruler(printer)

        printer.init()
        printer.text('\n***** das POS-Unternehmen *****\n')
        printer.text_center('Beleg-Nr. 10052/013/0001   31.08.2022 {:%x %X}\n'.format(datetime.now()))
        printer.text_center('Frau Tamara (Cashier) served you at Station 1\n')
        printer.text(ruler_single)
        printer.set_expanded(True)
        printer.justify_center()
        printer.text('RECEIPT #5678')
        printer.justify_left()
        printer.set_expanded(False)
        printer.text(ruler_single)


        item_mask = _build_item_mask(
                printer.feature.columns.condensed,
                alignments='><>^>>',
                column_widths=[
                    0.05,
                    0.2,
                    0.1,
                    0.05,
                    0.15,
                    0.15,
                ]
            )
        
                # Set the items sections
        for index, item in enumerate(receipt_data['items'], start=1):
            number = str(index)
            name = item['name']
            product_id = item['product_id']
            quantity = item['quantity']
            price = f"{item['price']:.2f}"
            total = f"{item['price'] * item['quantity']:.2f}"

        data = (
                ('No.', 'Product', 'Qty', '', 'Price', 'Total'),
                (f'{number}', 'SAMPLE', '2', 'x', '0.25', '0.50'),
                ('2', 'OTHER SAMPLE', '1', 'x', '1.50', '1.50'),
                ('3', 'ANOTHER ONE', '3', 'x', '0.75', '2.25'),
            )

        printer.set_condensed(True)
        for row in data:
            printer.text(item_mask.format(*row))

        printer.set_condensed(False)
        printer.text(ruler_single)
        printer.set_emphasized(True)
        printer.text('TOTAL  4.25')
        printer.set_emphasized(False)
        printer.text(ruler_single)
        printer.lf()
        
        # Set Footer of the receipt
        printer.text('\n')
        printer.ean13("1234567891011", barcode_height=100, barcode_width=200)
        printer.text_center('\n\n\n***** Thank you for your purchase *****\n')
        printer.text_center('www.aks-anker.de/')  
        
        # Cut the paper
        printer.cut()
        
        

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
    conn = USBConnection.create('04b8:0e20,ep_out=3,ep_in=0')
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
