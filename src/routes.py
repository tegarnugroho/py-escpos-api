import math

from datetime import datetime
from escpos import BluetoothConnection, barcode
from escpos.impl.epson import GenericESCPOS, CashDrawerException
from escpos import USBConnection, showcase
from flask import Blueprint, jsonify, request

app_routes = Blueprint('printer', __name__)

def _get_ruler(printer, char='-'):
    return char * printer.feature.columns.normal

def space(length_space):
    # Create a string of spaces with a specified length
    line = ' ' * length_space
    return line

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

        
        printer.set(align='center')
        # Set the print width to 80mm (ESC/POS command)
        printer.device.write(b'\x1B\x57\x40\x50')

        # Print receipt content
        printer.set(align='center')
        printer.writeText('\n***** das POS-Unternehmen *****\n\n')
        
        printer.writeText('Beleg-Nr. 10052/013/0001   31.08.2022 11:33:37\n')
        printer.set(align='left')
        printer.writeText('Frau Tamara (Cashier) served you at Station 1\n')
        printer.set(align='center')
        printer.text(ruler_single)
        
        # Define the column titles
        column_titles = ["Art-Nr", "Anz", "E-Preis", "Betrag"]

        # Set the items sections
        for index, item in enumerate(receipt_data['items'], start=1):
            number = str(index)
            name = item['name']
            product_id = item['product_id']
            quantity = item['quantity']
            price = f"{item['price']:.2f}"
            total = f"{item['price'] * item['quantity']:.2f}"

            # Calculate the space counts
            number_space_count = len(number)
            name_space_count = 44 - len(name)  # Adjust the space count as needed
            product_id_space_count = 18 - len(product_id)
            
            title_line = f"{space(3)}{column_titles[0]}{space(product_id_space_count + 4)}" \
                   f"{column_titles[1]}{space(3)}" \
                   f"{column_titles[2]}{space(3)}" \
                   f"{column_titles[3]}{space(3)}"

            if index == 1:
                printer.writeText(title_line + '\n')
                printer.writeText(ruler_single)

            name_line = f"{name}{space(name_space_count)}"
            qty_line = f"{quantity}{space(4)}"
            price_line = f"{price}{space(4)}"
            total_line = f"{total}"
            line = f"{number}{space(number_space_count)}" \
                   f"{name_line}"

            printer.writeText(line + '\n')
            printer.set(align='left')
            printer.writeText(f"{space(3)}{product_id}{space(product_id_space_count + 3)}{qty_line}{price_line}{total_line}\n")  # Print the product ID, quantity, price, and total below the name
            printer.set(align='center')
            
        # Accumulate the total amount 
        total_amount = sum(item['price'] * item['quantity'] for item in receipt_data['items'])
        total_amount = round(total_amount, 2)
        
        # Set total amount section
        printer.text(ruler_single)
        printer.set(text_type='B', font='A', width=2, height=2)  # Set larger size and bold format
        spaces_before_total = max(0, 24 - len(f"Gesamtbetrag {total_amount}"))  # Calculate the remaining spaces
        printer.writeText(f"Gesamtbetrag {space(spaces_before_total)}{total_amount}\n")
        printer.set(text_type='NORMAL', font='A', width=1, height=1) 
        printer.text(ruler_single)
        
        # Set the tax, net section
        task_rate = 19  # Task rate in percentage
        net_price = total_amount / (1 + (task_rate / 100))  # Calculate the net price
        task_amount = total_amount - net_price  # Calculate the task amount
        task_line = f"{space(10)}{task_rate:.1f}%: {task_amount:.2f}\n"
        net_price_line = f'Netto-Warenwert: {net_price:.2f}\n'
        printer.writeText(task_line)
        printer.writeText(net_price_line)
        printer.writeText(ruler_single)
        
        # Footer of the receipt
        printer.writeText('\n')
        printer.barcode("123456", "CODE39", pos='OFF', width=2, height=100)  # Generate the barcode without a number
        printer.writeText('\n\n\n***** Thank you for your purchase *****\n')
        printer.writeText('www.aks-anker.de/')

        # Cut the paper
        printer.cut()

        # Close the printer connection
        printer.close()

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
