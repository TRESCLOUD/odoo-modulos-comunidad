# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2013 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from barcode import barcode
from tools import translate
#from currency_to_text import currency_to_text
from ctt_objects import supported_language
import base64
import StringIO
from PIL import Image
import pooler
import time
import osv
import re
from report import report_sxw
from tools.translate import _
import netsvc
from tools.safe_eval import safe_eval as eval
from aeroolib.plugins.opendocument import _filter
import pytz, datetime
from string import upper
from operator import itemgetter
# TRESCLOUD EXTENDED
from trc_mod_python import amount_to_words_spanish

try:
    from docutils.examples import html_parts # use python-docutils library
except ImportError, e:
    rest_ok = False
else:
    rest_ok = True
try:
    import markdown
    from markdown import Markdown # use python-markdown library
    from markdown.inlinepatterns import AutomailPattern
    
    class AutomailPattern_mod (AutomailPattern, object):
        def __init__(self, *args, **kwargs):
            super(AutomailPattern_mod, self).__init__(*args, **kwargs)

        def handleMatch(self, m):
            el = super(AutomailPattern_mod, self).handleMatch(m)
            href = ''.join([chr(int(a.replace(markdown.AMP_SUBSTITUTE+'#', ''))) for a in el.get('href').split(';') if a])
            el.set('href', href)
            return el
    
    markdown.inlinepatterns.AutomailPattern = AutomailPattern_mod # easy hack for correct displaying in Joomla

except ImportError, e:
    markdown_ok = False
else:
    markdown_ok = True
try:
    from mediawiki import wiki2html # use python-mediawiki library
except ImportError, e:
    wikitext_ok = False
else:
    wikitext_ok = True

def domain2statement(domain):
    statement=''
    operator=False
    for d in domain:
        if not operator:
            if type(d)==str:
                if d=='|':
                    operator=' or'
                continue
            else:
                operator=False
        statement+=' o.'+str(d[0])+' '+(d[1]=='=' and '==' or d[1])+' '+(isinstance(d[2], str) and '\''+d[2]+'\'' or str(d[2]))
        if d!=domain[-1]:
             statement+=operator or ' and'
        operator=False
    return statement

class ExtraFunctions(object):
    """ This class contains some extra functions which
        can be called from the report's template.
    """
    #Global para realizar conteo ordenado
    _sequence_value = 0

    def __init__(self, cr, uid, report_id, context):
        self.cr = cr
        self.uid = uid
        self.pool = pooler.get_pool(self.cr.dbname)
        self.report_id = report_id
        self.context = context
        self.functions = {
            'asarray':self._asarray,
            'asimage':self._asimage,
            'html_embed_image':self._embed_image,
            'get_attachments':self._get_attachments,
            'get_name':self._get_name,
            'get_label':self._get_label,
            'getLang':self._get_lang,
            'get_selection_item':self._get_selection_items('item'),
            'safe':self._get_safe,
            'countif':self._countif,
            'count':self._count,
            'sumif':self._sumif,
            'sum_field':self._sum,
            'max_field':self._max,
            'min_field':self._min,
            'average':self._average,
            'large':self._large,
            'small':self._small,
            'count_blank':self._count_blank,
            '_':self._translate_text,
            'gettext':self._translate_text,
            'currency_to_text':self._currency2text(context['company'].currency_id.name), #self._currency2text(context['company'].currency_id.code),
            'barcode':barcode.make_barcode,
            'debugit':self.debugit,
            'dec_to_time':self._dec2time,
            'chunks':self._chunks,
            'browse':self._browse,
            'search':self._search,
            'search_ids':self._search_ids,
            'field_size':self._field_size,
            'field_accuracy':self._field_accuracy,
            'bool_as_icon':self._bool_as_icon,
            'time':time,
            'report_xml': self._get_report_xml(),
            'get_log': self._perm_read(self.cr, self.uid),
            'get_selection_items': self._get_selection_items(),
            'itemize': self._itemize,
            'html_escape': self._html_escape,
            'http_prettyuri': self._http_prettyuri,
            'http_builduri': self._http_builduri,
            'text_markdown': markdown_ok and self._text_markdown or \
                self._text_plain('"markdown" format is not supported! Need to be installed "python-markdown" package.'),
            'text_restruct': rest_ok and self._text_restruct or \
                self._text_plain('"reStructuredText" format is not supported! Need to be installed "python-docutils" package.'),
            'text_wiki': wikitext_ok and self._text_wiki or \
                self._text_plain('"wikimarkup" format is not supported! Need to be installed "python-mediawiki" package.'),
            'text_markup': self._text_markup,
            '__filter': self.__filter, # Don't use in the report template!
            # TRESCLOUD EXTENDED
            'search_extend': self._search_extend,
            'search_ids_extend': self._search_ids_extend,
            'read_ids': self._read_ids,
            'sum_field_search': self._sum_field_search,
            'group_and_sum': self._group_and_sum,
            'get_identification': self._get_identification,
            'convert_datetime_to_ECT': self._convert_datetime_to_ECT,
            'init_sequence': self._init_sequence,
            'next_sequence': self._next_sequence,
            'get_state_stock_move': self._get_state_stock_move,
            'get_text_upper': self._get_text_upper,
            'sum_operation_fields': self._sum_operation_fields,
            'operation_values': self._operation_values,
            'amount_to_word': self._amount_to_word,
            'float_as_string': self._float_as_string,
            
        }

    def _get_identification(self, vat):
        '''
        Verifica si es que la cedula o pasaporte hay que eliminar el 'EC'
        :param vat: Cedula a analizar
        :return: Devuelve la cedula ecuatoriana sin el ec si tuviera 'ec'
        '''
        if vat:
            rex_product_code = '^EC[0-9]{10}$|^EC[0-9]{13}$'
            regex = re.compile(rex_product_code, flags=re.IGNORECASE)
            if regex.match(vat):
                vat = vat[2:]
            else:
                vat = vat
        else:
            vat = 'Especifique identificacion correcta.'
        return vat
    
    def _convert_datetime_to_ECT(self, date_as_string):
        '''
        Convierte un string de datetime de Odoo a la hora del SRI (GMT -5)
        '''
        if not date_as_string:
            return '' #si no se pasa la fecha retornamos una cadena vacia para impresion
        #Odoo guarda las fechas en UTC, pero se requiere imprimir en GTM -5
        #Aeroo no maneja conversion de zonas horarias, creamos nuestro propio metodo para la conversion a GMT -5
        local = pytz.timezone("America/Guayaquil") #la zona horaria del SRI es GMT -5
        utc = pytz.utc
        format_time_str = "%Y-%m-%d %H:%M:%S.%f"
        try: #a veces el sri no responde con segundos 
            naive = datetime.datetime.strptime(date_as_string, format_time_str)
        except:
            try:
                format_time_str = "%Y-%m-%d %H:%M:%S"
                naive = datetime.datetime.strptime(date_as_string, format_time_str)
            except:
                format_time_str = "%Y-%m-%d"
                return date_as_string
        utc_dt = utc.localize(naive, is_dst=None)
        auth_date_in_local = utc_dt.astimezone (local)
        return auth_date_in_local.strftime (format_time_str)

    def __filter(self, val):
        if isinstance(val, osv.orm.browse_null):
            return ''
        elif isinstance(val, osv.orm.browse_record):
            return val.name_get({'lang':self._get_lang()})[0][1]
        return _filter(val)

    def _perm_read(self, cr, uid):
        def get_log(obj, field=None):
            if field:
                return obj.perm_read()[0][field]
            else:
                return obj.perm_read()[0]
        return get_log

    def _get_report_xml(self):
        return self.pool.get('ir.actions.report.xml').browse(self.cr, self.uid, self.report_id)

    def _get_lang(self, source='current'):
        if source=='current':
            return self.context['lang'] or self.context['user_lang']
        elif source=='company':
            return self.context['user'].company_id.partner_id.lang
        elif source=='user':
            return self.context['user_lang']

    def _bool_as_icon(self, val, kind=0):
        if isinstance(kind, (list, tuple)):
            if val==True:
                return kind [0]
            elif val==False:
                return kind[1]
            else:
                return kind[2]
        bool_kind = {0:{True:self._translate_text('True'), False:self._translate_text('False'), None:""},
                     1:{True:self._translate_text('T'), False:self._translate_text('F'), None:""},
                     2:{True:self._translate_text('Yes'), False:self._translate_text('No'), None:""},
                     3:{True:self._translate_text('Y'), False:self._translate_text('N'), None:""},
                     4:{True:'+', False:'-', None:""},
                     5:{True:'[ + ]', False:'[ - ]', None:"[ ]"},
                     6:{True:'[ x ]', False:'[ ]', None:"[ ]"},
                    }
        return bool_kind.get(kind, {}).get(val, val)

    def _dec2time(self, dec, h_format, min_format):
        if dec==0.0:
            return None
        elif int(dec)==0:
            return min_format.replace('%M', str(int(round((dec-int(dec))*60))))
        elif dec-int(dec)==0.0:
            return h_format.replace('%H', str(int(dec)))
        else:
            return h_format.replace('%H', str(int(dec)))+min_format.replace('%M', str(int(round((dec-int(dec))*60))))

    def _currency2text(self, currency):
        def c_to_text(sum, currency=currency, language=None):
            #return unicode(currency_to_text(sum, currency, language or self._get_lang()), "UTF-8")
            return unicode(supported_language.get(language or self._get_lang()).currency_to_text(sum, currency), "UTF-8")
        return c_to_text

    def _translate_text(self, source):
        trans_obj = self.pool.get('ir.translation')
        trans = trans_obj.search(self.cr,self.uid,[('res_id','=',self.report_id),('type','=','report'),('src','=',source),('lang','=',self.context['lang'] or self.context['user_lang'])])
        if not trans:
            #trans_obj.create(self.cr, self.uid, {'src':source,'type':'report','lang':self._get_lang(),'res_id':self.report_id,'name':('ir.actions.report.xml,%s' % source)[:128]})
            trans_obj.create(self.cr, self.uid, {'src':source,'type':'report','lang':self._get_lang(),'res_id':self.report_id,'name':'ir.actions.report.xml'})
        return translate(self.cr, 'ir.actions.report.xml', 'report', self._get_lang(), source) or source

    def _countif(self, attr, domain):
        statement = domain2statement(domain)
        expr = "for o in objects:\n\tif%s:\n\t\tcount+=1" % statement
        localspace = {'objects':attr, 'count':0}
        exec expr in localspace
        return localspace['count']

    def _count_blank(self, attr, field):
        expr = "for o in objects:\n\tif not o.%s:\n\t\tcount+=1" % field
        localspace = {'objects':attr, 'count':0}
        exec expr in localspace
        return localspace['count']

    def _count(self, attr):
        return len(attr)

    def _sumif(self, attr, sum_field, domain):
        statement = domain2statement(domain)
        expr = "for o in objects:\n\tif%s:\n\t\tsumm+=float(o.%s)" % (statement, sum_field)
        localspace = {'objects':attr, 'summ':0}
        exec expr in localspace
        return localspace['summ']

    def _sum(self, attr, sum_field):
        expr = "for o in objects:\n\tsumm+=float(o.%s)" % sum_field
        localspace = {'objects':attr, 'summ':0}
        exec expr in localspace
        return localspace['summ']

    def _max(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return max(localspace['value_list'])

    def _min(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return min(localspace['value_list'])

    def _average(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return float(sum(localspace['value_list']))/float(len(localspace['value_list']))

    def _asarray(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return localspace['value_list']

    def _get_name(self, obj):
        if obj.__class__==osv.orm.browse_record:
            return self.pool.get(obj._table_name).name_get(self.cr, self.uid, [obj.id], {'lang':self._get_lang()})[0][1]
        elif type(obj)==str: # only for fields in root record
            model = self.context['model']
            field, rec_id = obj.split(',')
            rec_id = int(rec_id)
            if rec_id:
                field_data = self.pool.get(model).fields_get(self.cr, self.uid, [field], context=self.context)
                return self.pool.get(field_data[field]['relation']).name_get(self.cr, self.uid, [rec_id], {'lang':self._get_lang()})[0][1]
            else:
                return ''
        return ''

    def _get_label(self, obj, field):
        if not obj:
            return ''
        try:
            if isinstance(obj, report_sxw.browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._table_name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                labels = self.pool.get(model).fields_get(self.cr, self.uid, allfields=[field], context=self.context)
                return labels[field]['string']
        except Exception, e:
            return ''

    def _field_size(self, obj, field):
        try:
            if isinstance(obj, report_sxw.browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._table_name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                size = self.pool.get(model)._columns[field].size
                return size
        except Exception, e:
            return ''

    def _field_accuracy(self, obj, field):
        try:
            if isinstance(obj, report_sxw.browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._table_name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                digits = self.pool.get(model)._columns[field].digits
                return digits or [16,2]
        except Exception:
            return []

    def _float_as_string(self, obj, field, value):
        '''
        Retorna un campo float pero como string con rellenado conforme el numero de decimales declarado en columns
        Ayuda a elaborar reportes donde se desea ver el campo con los mismos decimales que en openerp
        '''
        try:
            if isinstance(value, (float)):
                decimal_positions = self._field_accuracy(obj, field)[1]
                value_as_string = '{:.{prec}f}'.format(value, prec=decimal_positions)
                return value_as_string
            return value
        except Exception:
            return []

    def _get_selection_items(self, kind='items'):
        def get_selection_item(obj, field, value=None):
            try:
                if isinstance(obj, report_sxw.browse_record_list):
                    obj = obj[0]
                if isinstance(obj, (str,unicode)):
                    model = obj
                    field_val = value
                else:
                    model = obj._table_name
                    field_val = getattr(obj, field)
                if kind=='item':
                    if field_val:
                        return dict(self.pool.get(model).fields_get(self.cr, self.uid, allfields=[field], context=self.context)[field]['selection'])[field_val]
                elif kind=='items':
                    return self.pool.get(model).fields_get(self.cr, self.uid, allfields=[field], context=self.context)[field]['selection']
                return ''
            except Exception:
                return ''
        return get_selection_item

    def _get_attachments(self, o, index=None, raw=False):
        attach_obj = self.pool.get('ir.attachment')
        srch_param = [('res_model','=',o._name),('res_id','=',o.id)]
        if type(index)==str:
            srch_param.append(('name','=',index))
        attachments = attach_obj.search(self.cr,self.uid,srch_param)
        res = [x['datas'] for x in attach_obj.read(self.cr,self.uid,attachments,['datas']) if x['datas']]
        convert = raw and base64.decodestring or (lambda a: a)
        if type(index)==int:
            return convert(res[index])
        return convert(len(res)==1 and res[0] or res)

    def _asimage(self, field_value, rotate=None, size_x=None, size_y=None, uom='px', hold_ratio=False):
        def size_by_uom(val, uom, dpi):
            if uom=='px':
                result=str(val/dpi)+'in'
            elif uom=='cm':
                result=str(val/2.54)+'in'
            elif uom=='in':
                result=str(val)+'in'
            return result
        ##############################################
        if not field_value:
            return StringIO.StringIO(), 'image/png'
        field_value = base64.decodestring(field_value)
        tf = StringIO.StringIO(field_value)
        tf.seek(0)
        im=Image.open(tf)
        format = im.format.lower()
        dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))
        try:
            if rotate!=None:
                im=im.rotate(int(rotate))
                tf.seek(0)
                im.save(tf, format)
        except Exception, e:
            print e

        if hold_ratio:
            img_ratio = im.size[0] / float(im.size[1]) # width / height
            if size_x and not size_y:
                size_y = size_x / img_ratio
            elif not size_x and size_y:
                size_x = size_y * img_ratio
            elif size_x and size_y:
                size_y2 = size_x / img_ratio
                size_x2 = size_y * img_ratio
                if size_y2 > size_y:
                    size_x = size_x2
                elif size_x2 > size_x:
                    size_y = size_y2

        size_x = size_x and size_by_uom(size_x, uom, dpi_x) or str(im.size[0]/dpi_x)+'in'
        size_y = size_y and size_by_uom(size_y, uom, dpi_y) or str(im.size[1]/dpi_y)+'in'
        return tf, 'image/%s' % format, size_x, size_y

    def _embed_image(self, extention, img, width=0, height=0, raw=False) :
        "Transform a DB image into an embeded HTML image"
        if not img:
            return ''
        try:
            if width :
                width = ' width="%spx"'%(width)
            else :
                width = ''
            if height :
                height = 'height="%spx" '%(height)
            else :
                height = ''
            if raw:
                toreturn = 'data:image/%s;base64,%s' % (extention, ''.join(str(img).splitlines()))
            else:
                toreturn = '<img%s %ssrc="data:image/%s;base64,%s">' % (width, height, extention, str(img))
            return toreturn
        except Exception, exp:
            print exp
            return 'No image'

    def _large(self, attr, field, n):
        array=self._asarray(attr, field)
        try:
            n-=1
            while(n):
                array.remove(max(array))
                n-=1
            return max(array)
        except ValueError, e:
            return None

    def _small(self, attr, field, n):
        array=self._asarray(attr, field)
        try:
            n-=1
            while(n):
                array.remove(min(array))
                n-=1
            return min(array)
        except ValueError, e:
            return None

    def _chunks(self, l, n):
        """ Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    def _search_ids(self, model, domain):
        obj = self.pool.get(model)
        return obj.search(self.cr, self.uid, domain)

    def _search(self, model, domain):
        obj = self.pool.get(model)
        ids = obj.search(self.cr, self.uid, domain)
        return obj.browse(self.cr, self.uid, ids, {'lang':self._get_lang()})

    def _browse(self, *args):
        if not args or (args and not args[0]):
            return None
        if len(args)==1:
            model, id = args[0].split(',')
            id = int(id)
        elif len(args)==2:
            model, id = args
        else:
            raise None
        return self.pool.get(model).browse(self.cr, self.uid, id)

    def _get_safe(self, expression, obj):
        try:
            return eval(expression, {'o':obj})
        except Exception, e:
            return None

    def debugit(self, object):
        """ Run the server from command line and 
            call 'debugit' from the template to inspect variables.
        """
        import pdb;pdb.set_trace()
        return

    def _itemize(self, array, purefalse = False, base_num = 1):
        it = iter(array)
        falseval = purefalse and False or ''
        e = it.next()
        lind = 0
        while True:
            lind += 1
            is_even = lind%2 == 0 or falseval
            is_odd = not is_even or falseval
            is_first = lind == 1 or falseval
            try:
                nxt = it.next()
                yield (lind-1, lind+base_num-1, e, is_even, is_odd, is_first, falseval)
                e = nxt
            except StopIteration:
                yield (lind-1, lind+base_num-1, e, is_even, is_odd, is_first, True)
                break

    def _html_escape(self, s):
        toesc={ '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&apos;' }
        
        if type(s) is str:
            s.decode()
        try:
            return ''.join(map(lambda a: toesc.get(a, a), s))
        except TypeError:
           return s

    def _http_prettyuri(self, s):
        def do_filter(c):
            # filter out reserved and "unsafe" characters
            pos = '''<>$&+,/\:;=?@'"#%{}|^~[]()`'''.find(c)
            if pos >= 0: return False
            
            # filter out ASCII Control characters and unhandled Non-ASCII characters
            ordc = ord(c)
            if (ordc >= 0 and ordc <= 31) or (ordc >= 127 and ordc <= 255): return False
            return c

        if type(s) is str: s.decode()
        # tranlate specific latvian characters into latin and whitespace into dash
        tt = dict(zip(map(ord, 'āčēģīķļņōŗšūžĀČĒĢĪĶĻŅŌŖŠŪŽ '.decode()), 'acegiklnorsuzACEGIKLNORSUZ-'.decode()))
        try:
            s = s.translate(tt)
            return (filter(do_filter, s)).lower()
        except TypeError:
            return s

    def _http_builduri(self, *dicts):
        d = {}
        for ind in dicts:
            d.update(ind)
        result = ''
        for pair in d.iteritems():
            result += '&%s=%s' % pair
        return result

    def _text_restruct(self, text):
        output = html_parts(unicode(text), doctitle=False)
        return output['body']

    def _text_markdown(self, text):
        md = Markdown()
        return md.convert(text)

    def _text_wiki(self, text):
        return wiki2html(text, True)

    def _text_plain(self, msg):
        def text_plain(text):
            netsvc.Logger().notifyChannel('report_aeroo', netsvc.LOG_INFO, msg)
            return text
        return text_plain

    def _text_markup(self, text):
        lines = text.splitlines()
        first_line = lines.pop(0)
        if first_line=='text/x-markdown':
            return self._text_markdown('\n'.join(lines))
        elif first_line=='text/x-wiki':
            return self._text_wiki('\n'.join(lines))
        elif first_line=='text/x-rst':
            return self._text_rest('\n'.join(lines))
        return text

#
# TRESCLOUD
# Autor: Patricio Rangles
# Librerias extras para reporteria
# 
# NOTA: Context es muy útil, por ejemplo, en campos autocalculados, especificamente en productos indicando
# la bodega y las fechas iniciales y finles automaticamente indica el stock sin necesidad de calcular
# nuevamente. Deben existir más ejemplos de este estilo
#
    def _search_ids_extend(self, model, domain, order_by = None, count = False, context = None):
        obj = self.pool.get(model)
        return obj.search(self.cr, self.uid, domain, order=order_by, count=count, context = context)

    def _search_extend(self, model, domain, order_by = None, context = None):
        if not context:
            context = {}
        context['lang'] = self._get_lang()
        obj = self.pool.get(model)
        ids = self._search_ids_extend(model, domain, order_by=order_by, context = context)
        return obj.browse(self.cr, self.uid, ids, context = context)

    def _sum_field_search(self, model, domain, field, field_condition=None, condition_add=None, condition_substract=None, context=None):
        """
        Function return the sum values of a field using conditionary field and condition values:
        
        field: field to sum
        field_condition: field used like condition
        condition_add: list of condition to add values, if send True is in all other cases (else) 
        condition_substract: list of condition to substract values, if send True is in all other cases (else)
         
        """
        
        obj = self.pool.get(model)
        resul = self._search_extend(model, domain, context=context)

        expr = ""
        
        if field_condition:
         
            expr_for = "for o in objects:"
            expr_if_add = ""
            exp_if_subs = ""
            add_first_add = True
            add_first_subs = True
         
            if condition_add and type(condition_add)==type([]):
                #is a list, using in if
                expr_if_add = "\n    if o.%s in add:\n        summ = summ + float(o.%s)" % (field_condition, field)
            elif condition_add:
                expr_if_add = "\n    else:\n        summ = summ + float(o.%s)" % field
                add_first_add = False
            else:
                expr_if_add = ""
                add_first_add = False
            
            if condition_substract and type(condition_substract)==type([]):
                #is a list, using in if
                exp_if_subs = "\n    if o.%s in substract:\n        summ = summ - float(o.%s)" % (field_condition, field)
            elif condition_substract:
                exp_if_subs = "\n    else:\n        summ = summ - float(o.%s)" % field
                add_first_subs = False
            else:
                exp_if_subs = ""
                add_first_subs = False
        
            # caso partidular, ambas condiciones True
            if not add_first_add and not add_first_subs and condition_add and condition_substract:
                expr = "summ = 0"
            elif add_first_subs:
                expr = expr_for + exp_if_subs + expr_if_add
            else:
                expr = expr_for + expr_if_add + exp_if_subs
        else:
            expr = "for o in objects:\n    summ = summ + float(o.%s)" % field
      
        localspace = {
                'objects': resul,
                'add': condition_add,
                'substract': condition_substract, 
                'summ':0
                    }
        exec expr in localspace
        
        return localspace['summ']
            
    def _read_ids(self, model, ids, fields = None, context = None):
        if not context:
            context = {}
        context['lang'] = self._get_lang()
        obj = self.pool.get(model)
        return obj.read(self.cr, self.uid, ids, fields=fields, context=context)

    def _group_and_sum(self, list_to_group, field_group_by, fields_sum, order_result=False, order_asc=True):#, group_empty = False):
        """
        Group a list of items under this conditions:
        1) parameter list_to_group -> list of items to group by
        2) parameter field_group_by -> group by one field, this field is returned  
        3) parameter fields_sum -> List of fields to sum, this fields are returned
           If a field is string check if text is different and add the description, other case
           send one time the text
        4) parameter order_result -> Boolean value that indicate the list must be order, else the returned 
           list items not have any order in particular
        5) parameter order_asc -> Boolean value that indicate the list must be order in ascendent mode, 
           else order in reverse  
        6) if field to group is False, if is blank o null they are independent values, don't group
        7) the rest of fields are ignored
        
        -----------
        TODO (Next revision):    
        4) parameter group_empty -> allow the funcion to group empty, None or null values in one line
           if False, if is blank o null they are independent values, don't group 
        5) the rest of fields are ignored

        """
        groups = []
        for item in list_to_group:
            # Se requiere iterar varias veces dependiendo los niveles de puntuacion
            split_atributo = field_group_by.split('.')
            actual = item

            for atrib in split_atributo:
                actual = getattr(actual, atrib, None)
            
            group_exist= False
            
            if actual is not None:
                for group in groups:
                    if group[field_group_by] == actual:
                        group_exist = True
                        # ya existe, sumo los valores
                        #sums = group['sums']
                        for field in fields_sum:
                            actual_sum = getattr(item, field, None) 
                            if isinstance(group[field],basestring):
                                # es texto, verifico si el anterior es igual
                                if group[field] != actual_sum:
                                    if group[field] != "":
                                        group[field] = group[field] + ", " + actual_sum
                                    else: 
                                        group[field] = actual_sum 
                                ##Grabo el ultimo texto
                                #group[field] = actual_sum  
                            else:
                                # es numerico, sumo
                                group[field] = group[field] + actual_sum  
                        break

            if not group_exist:
                # no existe, agrego las sumas
                group = {}
                group[field_group_by] = actual 
                for field in fields_sum:
                    group[field] = getattr(item, field, None) 
                
                groups.append(group)
        # Esta parte ordena dependiendo si es ascendente o descendente
        #sorted(groups, key=lambda group: group[field_group_by])
        if order_result:
            return sorted(groups, key=itemgetter(field_group_by), reverse=not order_asc)
        else:
            return groups

    def _init_sequence(self, initial_value=0):
        '''
        This function set the initial value to count
        :param initial_value: initial value
        '''
        self._sequence_value = initial_value        

    def _next_sequence(self):
        '''
        This function add 1 and return the next value
        '''
        self._sequence_value = self._sequence_value + 1
        return self._sequence_value
    
    def _get_state_stock_move(self, state):
        '''
        Este método devuelve el estado de un stock_move
        :param state: Estado de un stock_move
        '''
        if state == 'done':
            return 'Realizado'
        elif state == 'assigned':
            return 'Reservado'
        elif state == 'cancel':
            return 'Cancelado'
        elif state == 'received':
            return 'Recibido'
        elif state == 'ready_to_receive':
            return 'Listo para recibir'
        elif state == 'draft':
            return 'Borrador'
        elif state == 'auto':
            return 'Esperando otra operación'
        elif state == 'confirmed':
            return 'Esperando disponibilidad'
        return ''
    
    def _get_text_upper(self, text):
        '''
        Este método convierte un texto a MAYÚSCULAS
        '''
        new_text = ''
        if text:
            new_text = upper(unicode(text))
        return new_text

    def _sum_operation_fields(self, attr, field_a, field_b, operand='*'):
        '''
        This function sum the operation between 2 fields, by default the opration is
        multiplication '*'
        :param attr: list to operate
        :param field_a: name of field to use as operand a
        :param field_b: name of field to use as operand b
        :param operand: operand to use, can be any mathematical operand like *, /, +, - %
        '''
        expr = "for o in objects:\n\tsumm+=float(o.%s) %s float(o.%s)" %(field_a, operand, field_b)
        localspace = {'objects':attr, 'summ':0}
        exec expr in localspace
        return localspace['summ']
    
    def _operation_values(self, field_a, field_b, operand='*'):
        '''
        This function sum the operation between 2 fields, by default the opration is
        multiplication '*'
        :param field_a: name of field to use as operand a
        :param field_b: name of field to use as operand b
        :param operand: operand to use, can be any mathematical operand like *, /, +, - %
        '''
        expr = "summ+=float(o.%s) %s float(o.%s)" %(field_a, operand, field_b)
        localspace = {'summ':0}
        exec expr in localspace
        return localspace['summ']

    def _amount_to_word(self, value, language='spanish', context=None):
        '''
        This function transform the amount total in text using the select language
        :param value: numeric value to transform
        :param language: text indicating the languaje to use, spanish predefined 
        '''
        context = context or {}
        languages_function = {
            'spanish': amount_to_words_spanish.amount_to_words_es
            }
        convert_text = languages_function.get(language, False)
        if not convert_text:
            convert_text = amount_to_words_spanish.amount_to_words_es
        return convert_text(value)
    