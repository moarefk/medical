# -*- coding: utf-8 -*-
##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2004-TODAY Tech-Receptives(<http://www.techreceptives.com>)
#    Special Credit and Thanks to Thymbra Latinoamericana S.A.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from datetime import datetime

from openerp.osv import fields, orm

from openerp.addons.oemedical.oemedical_constants import hours, minutes

HISTORY_ACTION_FORMAT = "-" * 32 + "  %s  " + "-" * 32 + "\n"


class OeMedicalAppointment(orm.Model):
    _name = 'oemedical.appointment'

    _columns = {
        'user_id': fields.many2one(
            'res.users',
            'Responsible', readonly=True,
            states={'draft': [('readonly', False)]}),
        'patient_id': fields.many2one(
            'oemedical.patient', string='Patient',
            required=True, select=True,
            help='Patient Name'),
        'name': fields.char(
            string='Appointment ID',
            size=256,
            readonly=True),
        'appointment_date': fields.datetime(string='Date and Time'),
        'appointment_day': fields.date(string='Date'),
        'appointment_hour': fields.selection(hours,
                                             string='Hour'),
        'appointment_minute': fields.selection(minutes,
                                               string='Minute'),

        'duration': fields.float('Duration'),
        'doctor': fields.many2one(
            'oemedical.physician',
            string='Physician', select=True,
            help="Physician's Name"),
        'alias': fields.char(
            string='Alias',
            size=256),
        'comments': fields.text(string='Comments'),
        'appointment_type': fields.selection([
            ('ambulatory', 'Ambulatory'),
            ('outpatient', 'Outpatient'),
            ('inpatient', 'Inpatient'),
        ], string='Type'),
        'institution': fields.many2one(
            'res.partner',
            string='Health Center',
            help='Medical Center',
            domain="[('is_institution', '=', True)]"),
        # 'institution': fields.related('user_id','parent_id', type='many2one'
        # , relation='res.partner', string='Institution', store=True, domain="
        # [('is_institution', '=', True)]"), #, readonly=True
        'consultations': fields.many2one(
            'product.product',
            string='Consultation Services',
            help='Consultation Services',
            domain="[('type', '=', 'service'), ]"),
        'urgency': fields.selection([
            ('a', 'Normal'),
            ('b', 'Urgent'),
            ('c', 'Medical Emergency'), ],
            string='Urgency Level'),
        'speciality': fields.many2one('oemedical.specialty',
                                      string='Specialty',
                                      help='Medical Specialty / Sector'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('waiting', 'Wating'),
            ('in_consultation', 'In consultation'),
            ('done', 'Done'),
            ('canceled', 'Canceled'),
        ],
            string='State'),
        'history_ids': fields.one2many(
            'oemedical.appointment.history', 'appointment_id_history',
            'History lines', states={'start': [('readonly', True)]}),

    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool['ir.sequence'].get(
            cr, uid, 'oemedical.appointment'),
        'duration': 30.00,
        'urgency': 'a',
        'state': 'draft',
        'user_id': lambda s, cr, u, c: u,
    }

    def create(self, cr, uid, vals, context=None):
        val_history = {}
        date_time_str = vals['appointment_day'] + ' ' + \
            vals['appointment_hour'] + ':' + vals['appointment_minute']
        vals['appointment_date'] = datetime.strptime(
            date_time_str, '%Y-%m-%d %H:%M')

        val_history = {
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to Confirm"
        }
        vals['history_ids'] = val_history

        return super(OeMedicalAppointment, self
                     ).create(cr, uid, vals, context=context)

    def button_back(self, cr, uid, ids, context=None):

        val_history = {}
        ait_obj = self.pool.get('oemedical.appointment.history')

        for order in self.browse(cr, uid, ids, context=context):
            if order.state == 'confirm':
                self.write(cr, uid, ids, {'state': 'draft'}, context=context)
                hist_action = "Changed to Draft"
            if order.state == 'waiting':
                hist_action = "Changed to Confirm"
                self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
            if order.state == 'in_consultation':
                hist_action = "Changed to Waiting"
                self.write(cr, uid, ids, {'state': 'waiting'}, context=context)
            if order.state == 'done':
                hist_action = "Changed to In Consultation"
                self.write(
                    cr, uid, ids, {'state': 'in_consultation'},
                    context=context)
            if order.state == 'canceled':
                hist_action = "Changed to Draft"
                self.write(cr, uid, ids, {'state': 'draft'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': hist_action
        }

        ait_obj.create(cr, uid, val_history)

        return True

    def button_confirm(self, cr, uid, ids, context=None):

        ait_obj = self.pool.get('oemedical.appointment.history')

        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to Waiting"
        }
        ait_obj.create(cr, uid, val_history)

        return True

    def button_waiting(self, cr, uid, ids, context=None):

        ait_obj = self.pool.get('oemedical.appointment.history')

        self.write(cr, uid, ids, {'state': 'waiting'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to Waiting"
        }
        ait_obj.create(cr, uid, val_history)

        return True

    def button_in_consultation(self, cr, uid, ids, context=None):

        ait_obj = self.pool.get('oemedical.appointment.history')

        self.write(cr, uid, ids, {'state': 'in_consultation'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to In Consultation"
        }
        ait_obj.create(cr, uid, val_history)

        return True

    def button_done(self, cr, uid, ids, context=None):

        val_history = {}
        ait_obj = self.pool.get('oemedical.appointment.history')

        self.write(cr, uid, ids, {'state': 'done'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to Done",
        }
        ait_obj.create(cr, uid, val_history)

        return True

    def button_cancel(self, cr, uid, ids, context=None):

        ait_obj = self.pool.get('oemedical.appointment.history')

        self.write(cr, uid, ids, {'state': 'canceled'}, context=context)

        val_history = {
            'appointment_id_history': ids[0],
            'name': uid,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'action': HISTORY_ACTION_FORMAT % "Changed to Canceled"
        }
        ait_obj.create(cr, uid, val_history)

        return True


class OeMedicalAppointment_history(orm.Model):
    _name = 'oemedical.appointment.history'

    _columns = {
        'appointment_id_history': fields.many2one(
            'oemedical.appointment',
            'History', ondelete='cascade'),
        'date': fields.datetime(string='Date and Time'),
        'name': fields.many2one('res.users', string='User', help=''),
        'action': fields.text('Action'),
    }
