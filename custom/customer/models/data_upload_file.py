from odoo import models, fields, api

class DataUploadFile(models.Model):
    _name = 'data.upload.file'
    _description = 'Data Upload File'
    
    name = fields.Char(string='Name', required=True)
    file = fields.Binary(string='File')
    file_type = fields.Char('File Type')
    
    date = fields.Datetime('Uploaded Date', default=lambda self: fields.Datetime.now())
    upload_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)

    upload_member_ids = fields.One2many('upload.member.line', 'upload_file_id', string='Members')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('done', 'Done')
    ], string='Status', default='draft')

    def action_validate_policy_data(self):
        # Check for customer_code matches and update upload_member_status
        for member_line in self.upload_member_ids:
            if not member_line.vehicle_chasis_no or not member_line.member_name or not member_line.country or not member_line.member_expiry_date:
                # Update upload_member_status to 'rejection' and add a remark
                member_line.update({'upload_member_status': 'rejection', 'comment': "*empty"})

            else:
                print("MEMBER LINE CUSTOMER CODE------",member_line.customer_code)
                matching_partner = self.env['res.partner'].search([
                    ('customer_code', '=', member_line.customer_code),
                ])
                member_list = self.env['res.partner'].search([
                    ('parent_customer_id','=', matching_partner.id)
                ])
                print("POICY MEMBER OF SPECIFIC CUSTOMER--------",member_list.id)
                if matching_partner and member_list: # if Customer_code matches , Same insurance company , Customer code matches, move to next checks

                    print("CHASIS NUMBER MATCH FROM EXCEL---- MEMBER LINE-------",member_line.vehicle_chasis_no)
                    print("CHASIS NUMBER MATCH FROM -----RES.PARTNER-------",member_list.vehicle_chasis_no)
                    
                    if member_list.vehicle_chasis_no == member_line.vehicle_chasis_no:  # If Vehicle Chasis Number Matches , Moves to name check , Check if the name matches
                        
                        print("VEHICLE CHAIS CHECK -----PASS-----")
                        
                        print("NAME MATCH FROM -----RES.PARTNER------- ",member_list.name)
                        print("NAME MATCH FROM EXCEL---- MEMBER LINE-------",member_line.member_name)
                        
                        if member_list.name == member_line.member_name:    # Name matches, check membership_state
                            print("NAME CHECK -----PASS-----")

                            print("MEMBERSHIP STATE CHECK : " ,member_list.membership_state)
                            
                            if member_list.membership_state == 'temp':            #temp , confirm , cancel 3  statuses are there
                                member_line.update({'upload_member_status': 'new','comment': "Exist Under Temp,*Overwrite"})   # If same comp , same member , Exist in temp , save as new Membership.
                            
                            elif member_list.membership_state == 'confirm':
                                # Calculate difference between member_expiry_date and member_activate_date
                                expiry_date = fields.Date.from_string(member_line.member_expiry_date)
                                activate_date = fields.Date.from_string(member_line.member_activate_date)
                                difference = (expiry_date - activate_date).days

                                print("EXPIRY DATE----",expiry_date)
                                print("ACTIVATION DATE------",activate_date)
                                print("DIFFRENCE CALCULATED---++++++++--",difference)
                                
                                print("EXPIRY DATE IN ---res.partner",member_list.member_expiry_date)
                                print("EXPIRY DATE IN ---excel",member_line.member_expiry_date)

                                if member_list.member_expiry_date != member_line.member_expiry_date:
                                    if difference >= 365:  # 12 months or above
                                        print("=-==-==--=-MEMBERSHIP RENEWAL--=-==-=")
                                        member_line.update({'upload_member_status': 'renewal','comment': "*Membership Renewal"})
                                    else:
                                        print("=-==-==--=-MEMBERSHIP EXTENSION--=-==-=")
                                        member_line.update({'upload_member_status': 'update','comment': "*Membership Extension"})
                                else :
                                     member_line.update({'upload_member_status': 'rejection', 'comment': "*Duplicate Record in System!"}) #Company Doesnt exist , so Rejection.          
                        else:
                            print("-=-==-==--=--=-==-==--=-NAME CHECK FAIL--=-==-==--=-=-==-==--=-=-==-==--=")  # Name doesn't match, update upload_member_status to 'new'
                            member_line.update({'upload_member_status': 'new' ,'comment': "Member Not Exist`"}) # If name  does not match, that is Member does to exist under Same company ,New Membership
                    else:
                        print("-=-==-==--=-=-==-==--=VEHICLE CHASIS CHECK FAIL-=-==-==--=-=-==-==--=-=-==-==--=")
                        member_line.update({'upload_member_status': 'new','comment': "*New Member"}) # if Vehicle Chasis Number  does not Match : Need to save as new rec , New membership
                else:
                    # No matching partner found, update upload_member_status to 'Rejected Member'
                    member_line.update({'upload_member_status': 'rejection', 'comment': "Company Not Found!"}) #Company Doesnt exist , so Rejection.
                    
        # Implement the validation logic here
        self.state = 'validate'


    def apply_member_upload_wizard(self):
        # Implement the logic to create/update res.partner records
        self.state = 'done'

    def action_cancel(self):
        self.state = 'draft'
    
    def action_delete_members(self):
        pass
    
    def action_view_rejected_records(self):
        pass

class UploadMemberLine(models.Model):
    _name = 'upload.member.line'
    _description = 'Upload Member Line'

    upload_file_id = fields.Many2one('data.upload.file', string='Upload File')
    
    member_name = fields.Char(string='Name')
    mobile = fields.Char(string='Mobile')
    
    vehicle_plate = fields.Char(string='Vehicle Plate')
    vehicle_chasis_no = fields.Char(string='Vehicle Chassis No')
    member_activate_date = fields.Date(string='Member Activate Date')
    member_expiry_date = fields.Date(string='Member Expiry Date')
    invoice_ref_date = fields.Date(string='Invoice Reference Date')
    customer_code = fields.Char(string='Customer Code')
    package = fields.Char(string='Package ID')
    # --------------------------------------------------------------------
    # Created
    member_type = fields.Selection([
        ('policy', 'Policy Member'),
        ('credit', 'Credit Member')
    ], string='Member Type')

    upload_member_status = fields.Selection([
        ('new', 'New Member'),
        ('rejection', 'Rejected Member'),
        ('renewal', 'Renewal Member'),
        ('update', 'Update Member')
    ], string='Upload Status')
    # --------------------------------------------------------------------
    customer_ref_date = fields.Date(string='Customer Reference Date')
    old_membership_number = fields.Char(string='Old Membership Number')
    policy_no = fields.Char(string='Policy No')
    
    vehicle_type = fields.Char('vehicle_type') 
    vehicle_model = fields.Char('vehicle_model')
    mail_ref = fields.Char('mail_ref') 

    vehicle_mfg_year = fields.Char(string='Vehicle Manufacturing Year')
    vehicle_reg_code = fields.Char(string='Vehicle Registration Code')
   
    street = fields.Char(string='Street')
    zip = fields.Char('zip') #Created
    
    delivery_ref_date = fields.Date(string='Delivery Reference Date')
    comment = fields.Text(string='Comment')
    sequence_code = fields.Char(string='Sequence Code')


    card_type = fields.Char('Card Type')
    state = fields.Char('State')
    country = fields.Char('Country')
    region_code = fields.Char('Region Code')
    vehicle_reg_country = fields.Char('Vehicle Reg Country')
    vehicle_emirate = fields.Char('Vehicle Emirate')
