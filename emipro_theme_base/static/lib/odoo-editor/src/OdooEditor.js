/** @odoo-module **/

import { OdooEditor } from "@web_editor/../lib/odoo-editor/src/OdooEditor";
import { patch } from "web.utils";
import { isEmptyBlock } from "@web_editor/../lib/odoo-editor/src/utils/utils";

patch(OdooEditor.prototype, "emipro_theme_base/static/lib/odoo-editor/src/OdooEditor.js", {
    _onKeyDown(ev) {
        this.functionCommon(ev)
    },
    _onInput(ev) {
        this.functionCommon(ev)
    },
    _onMouseUp(ev) {
        this.functionCommon(ev)
    },
    _onMouseDown(ev){
        this.functionCommon(ev)
    },
    _onDocumentKeydown(ev){
        this.functionCommon(ev)
    },
    _onDocumentKeyup(ev){
        this.functionCommon(ev)
    },
    functionCommon(ev){
        if($('#product_configure_model').hasClass('show') == true || $('#image_hotspot_configure_model').hasClass('show') == true){
            if($(ev.target).hasClass('product_configure_model_close') == true || $(ev.target).hasClass('image_hotspot_configure_model_close') == true){
                this._super.apply(ev, arguments);
            }
        }
        else{
            this._super.apply(ev, arguments);
        }
    },
});
