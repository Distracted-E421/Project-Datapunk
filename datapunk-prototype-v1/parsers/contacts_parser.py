import csv
import vobject
from base_parser import BaseParser

class ContactsParser(BaseParser):
    def parse_contacts_csv(self, filepath):
        self.connect_to_db()
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                query = """
                INSERT INTO contacts (
                    name, photo, group_membership, email, im, phone, address, organization,
                    relation, external_id, website, event, custom_field, notes, location,
                    birthday, hobby, gender, occupation, priority, sensitivity,
                    billing_information, directory_server, mileage, subject
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    row.get('Name'), row.get('Photo'), row.get('Group Membership'), row.get('Email'),
                    row.get('IM'), row.get('Phone'), row.get('Address'), row.get('Organization'),
                    row.get('Relation'), row.get('External Id'), row.get('Website'), row.get('Event'),
                    row.get('Custom Field'), row.get('Notes'), row.get('Location'), row.get('Birthday'),
                    row.get('Hobby'), row.get('Gender'), row.get('Occupation'), row.get('Priority'),
                    row.get('Sensitivity'), row.get('Billing Information'), row.get('Directory Server'),
                    row.get('Mileage'), row.get('Subject')
                )
                self.execute_query(query, values)
        self.close_db_connection()

    def parse_contacts_vcard(self, filepath):
        self.connect_to_db()
        with open(filepath, 'r', encoding='utf-8') as file:
            vcard = vobject.readOne(file)
            # Extract fields from the vCard object
            name = vcard.fn.value if hasattr(vcard, 'fn') else None
            email = vcard.email.value if hasattr(vcard, 'email') else None
            phone = vcard.tel.value if hasattr(vcard, 'tel') else None
            address = vcard.adr.value if hasattr(vcard, 'adr') else None
            organization = vcard.org.value[0] if hasattr(vcard, 'org') else None
            birthday = vcard.bday.value if hasattr(vcard, 'bday') else None
            notes = vcard.note.value if hasattr(vcard, 'note') else None

            query = """
            INSERT INTO contacts (
                name, email, phone, address, organization, birthday, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (name, email, phone, address, organization, birthday, notes)
            self.execute_query(query, values)
        self.close_db_connection()

print("Contact parsing module ready!")