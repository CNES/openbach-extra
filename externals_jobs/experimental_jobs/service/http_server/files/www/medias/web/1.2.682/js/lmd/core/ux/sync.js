/**
 * Script de publicité appelé en synchrone
 * juste avant le </body>
 */

if (typeof lmd === "undefined" || ! lmd) {
   lmd = {};
}

(function(lmd) {
   var global = (function () { return this; }());

   lmd.advertController = {
      /* liste de fonctions de callback sous forme : cle = id de format, valeur = tableau de fonctions */
      callbacks: [],
      /* liste des positions sur lesquelles les callbacks ont deja ete appeles,
       * la valeur est un objet {id: int, hasAd: bool} avev id = id de la position pub et hasAd indique si de la pub est présente
      */
      handled_ads: [],
      /* ajoute un callback sur une position pub */
      addCallback: function (format_label, pageid, callback) {
         var format_id, e, query;

         /* temporaire - gestion transition */
         if (callback === undefined && typeof pageid === "function") {
            callback = pageid;
            pageid = null;
         }

         query = '[data-adformat="' + format_label + '"]';
         if (pageid !== null) {
            query += '[data-adpage="' + pageid + '"]';
         }

         e = document.querySelector(query);
         if (!e) {
            return;
         }
         format_id = e.getAttribute('data-adformat-id');
         if (!format_id) {
            return;
         }
         /* si la pub est déjà chargée (handleAd déjà appelé pour ce format),
          * on execute le callback directement
         */
         if (this.handled_ads[format_id] !== undefined) {
            callback.call(e, this.handled_ads[format_id]);
            return;
         }

         /* initialisation */
         if (this.callbacks[format_id] === undefined) {
            this.callbacks[format_id] = [];
         }
         /* si la pub n'est pas chargée, on met en file d'attente */
         this.callbacks[format_id].push(callback);
      },
      /*
       * fonction appelee par smart lorsqu'une position pub est chargee
       * f : object de forme {id: int, hasAd: bool}
       *
       * Attention : pour que ça fonctionne correctement, si plusieurs positions sont présentes avec le même
       * data-adformat-id pour des pageid différents, il faut être sûr qu'une seule est "buildée" c'est à dire
       * contienne un div enfant d'id sas_[formatid]. Sinon outre que ce n'est pas HTML-compliant, le callback
       * peut être appelé sur le mauvais élément
       */
      handleAd: function (f) {
         var e, i, il,
             getPosition = function (formatid) {
                var list, e, i, nb;
                /* on recupere toutes les positions avec l'id donne
                 * pour ne traiter que celui qui a bien un sas_formatid enfant
                */
                list = document.querySelectorAll('[data-adformat-id="' + f.id + '"]');

                if (!list) {
                   return null;
                }

                nb = list.length;

                for(i = 0; i < nb; i++) {
                   e = list[i].querySelector('#sas_' + formatid);
                   if (e) {
                      return list[i];
                   }
                }

                return null;
             };
         /* position pub déjà traitée -> on sort */
         if (this.handled_ads[f.id] !== undefined) {
            return;
         }

         e = getPosition(f.id);
         if (e) {
            this.handled_ads[f.id] = f;
            if (this.callbacks[f.id] !== undefined) {
               il = (this.callbacks[f.id]).length;
               for (i = 0; i < il; i++) {
                  (this.callbacks[f.id][i]).call(e, f);
               }
            }
         }
      },
      /*
       * Indique si une position pub est déjà initialisee
       */
      existPositionAdvert: function(formatid) {
        return document.getElementById("sas_" + formatid) !== null;
      },
      /*
       * Construit une position pub
       * Attention sur une page donnée, si plusieurs positions partagent le même formatid (par-ex avec des pageid
       * différents pour de l'overlay ou du carousel), il faut s'assurer qu'une seule est buildée
       */
      buildPositionAdvert: function(params) {
         // callback pour gerer l'affichage de la position pub
         var pageid = params[0],
            sas_formatid = params[1],
            buildSasContainer = function (pageid, sas_formatid) {
               var parent = document.querySelector('[data-adformat-id="' + sas_formatid + '"][data-adpage="' + pageid + '"]'),
                  child = document.createElement('div');

               if (! parent) {
                  return;
               }
               child.id = 'sas_' + sas_formatid;
               parent.appendChild(child);

               return parent;
            },
            parent,
            sas_siteid,
            sas_target,
            sas_formatlabel;

         if (! global.SmartAdServerAjaxOneCall || this.existPositionAdvert(sas_formatid)) {
            return;
         }

         parent = buildSasContainer(pageid, sas_formatid);

         if (! parent) {
            return;
         }

         sas_siteid = parent.attributes.getNamedItem('data-adsite').value;
         sas_target = parent.attributes.getNamedItem('data-adquery').value;
         sas_formatlabel = parent.attributes.getNamedItem('data-adformat').value;

         global.SmartAdServerAjaxOneCall(sas_siteid + '/' + pageid, sas_formatid, sas_target);

         /* permet de gérer l'affichage des pubs en fonction de si elles sont remplies ou non */
        this.addCallback(sas_formatlabel, pageid, function (f) {
            if (f.hasAd) {
                // Used to display ads, which are hidden by default
                // relies on a class name to simplify Afrique breakpoints
                this.className += ' sold';
            }
        });
      },
      /*
       * Rafraichit une position pub
       */
      refresh: function(formatlabel, pageid) {
         var query, container, format_id;

         query = '[data-adformat="' + formatlabel + '"]';
         if (pageid) {
            query += '[data-adpage="' + pageid + '"]';
         }

         container = document.querySelector(query);

         if (container && container.attributes.length > 0 && container.attributes.getNamedItem('data-adformat-id') && global.sas_callAd) {
            format_id = container.attributes.getNamedItem('data-adformat-id').value;
            this.handled_ads[format_id] = undefined;
            global.sas_callAd(format_id);
         }
      },
      /*
       * Vide toutes les positions pub
       */
      cleanAll: function() {
         var parents,
            i;

         if (! global.sas_cleanAds) {
            return;
         }

         /* ré-initialisation des listes de callback / appels de callback */
         this.callbacks = [];
         this.handled_ads = [];

         /* fonction native de smart */
         global.sas_cleanAds();

         /* nettoyage */
         global.sas_fa = [];

         /* nettoyage des conteneurs smart */
         parents = document.querySelectorAll('[data-adformat-id]');
         for(i = 0; i < parents.length; i++) {
            parents[i].innerHTML = '';
            parents[i].style.display = 'none';
         }
      },
      /*
       * Construit toutes les positions pub pour une page donnee
       */
      buildAll: function(pageid) {
         global.sas_pageid = lmd.context.page.advert.smart.site + '/' + pageid;

         var parents = document.querySelectorAll('[data-adpage="' + pageid + '"]'),
             i;
         for(i = 0; i < parents.length; i++) {
            this.buildPositionAdvert([pageid, parents[i].attributes.getNamedItem('data-adformat-id').value]);
         }
      },
      /*
       * Rafraichit toutes les positions pub
       */
      refreshAll: function() {
         if (! global.sas_callAds) {
            return;
         }

         this.handled_ads = [];
         global.sas_callAds();
      }
   };
})(lmd);


(function(smart_recorded_positions, initFunction) {
   var global = (function () { return this; }()),
       initFunction = initFunction || function() {},
       getUserType = function() {
           try {
               var info_user_web = (document.cookie.match("(^|; )info_user_web=([^;]*)") || 0)[2];

               if (info_user_web !== undefined && info_user_web !== null && info_user_web !== "") {
                   info_user_web = JSON.parse(decodeURIComponent(info_user_web));

                   if (info_user_web !== undefined && info_user_web !== null && info_user_web !== "") {
                       return info_user_web.info_user.type_abo_oas;
                   }
               }
           } catch (e) {
               console.debug('error while accessing document.cookie : ' + e.message);
           }

           return null;
       },
       getElementRubriques = function () {
          var rubriques = [],
             il,
             i;

          if (global.lmd !== undefined &&
             global.lmd.context !== undefined &&
             global.lmd.context.pageType === "Element" &&
             global.lmd.context.rubriques !== undefined &&
             global.lmd.context.rubriques !== null) {

             il = global.lmd.context.rubriques.length;
             for(i = 0; i < il; i++) {
                rubriques.push(global.lmd.context.rubriques[i].url_friendly);
             }
          }

          return rubriques;
       },
       getElementId = function () {
          if (global.lmd !== undefined &&
             global.lmd.context !== undefined &&
             global.lmd.context.item !== undefined &&
             global.lmd.context.item !== null &&
             global.lmd.context.item.id !== undefined &&
             global.lmd.context.item.id !== null) {

             return global.lmd.context.item.id;
          }

          return null;
       },
       articleHasAtomeVideo = function () {
          if (global.lmd !== undefined &&
             global.lmd.context !== undefined &&
             global.lmd.context.item !== undefined &&
             global.lmd.context.item !== null &&
             global.lmd.context.item.has_atome_video !== undefined &&
             global.lmd.context.item.has_atome_video !== null) {
             return global.lmd.context.item.has_atome_video;
          }
          return false;
       },
       articleIsLongform = function () {
           if (global.lmd !== undefined &&
               global.lmd.context !== undefined &&
               global.lmd.context.item !== undefined &&
               global.lmd.context.item !== null &&
               global.lmd.context.item.gabarit !== undefined) {
               return global.lmd.context.item.gabarit === "singlecol";
           }
           return false;
       },
       articleType = function () {
           if (global.lmd !== undefined &&
               global.lmd.context !== undefined &&
               global.lmd.context.item !== undefined &&
               global.lmd.context.item !== null &&
               global.lmd.context.item.type !== undefined &&
               global.lmd.context.item.type.libelle !== undefined) {
               return global.lmd.context.item.type.libelle;
           }
           return false;
       },
       isAdvertActive = function () {
           // Pub activée ou non en fonction de la conf
           var active = global.lmd.conf.fsw.pub;

           //Pub désactivée pour les pages d'erreur type 404 et pour les pages sélectionnées
           if (global.lmd.context !== undefined &&
               global.lmd.context.page !== undefined &&
               global.lmd.context.page.advert !== undefined &&
               global.lmd.context.page.advert.active !== undefined &&
               ! global.lmd.context.page.advert.active) {

               active = false;
           }

           // Desactiver la publicite pour l'Education Nationale (les ENT)
           try {
               if (localStorage !== undefined && localStorage !== null && localStorage.user !== undefined) {
                   user = JSON.parse(localStorage.user);
                   if (user !== undefined &&
                       user.data !== undefined &&
                       user.data.services !== undefined &&
                       user.data.services.indexOf('educ_desactivation_pub') > -1) {

                       active = false;
                   }
               }
           } catch(e) {
               console.debug('error while accessing localStorage : ' + e.message);
           }

           return active;
       },
       getCurrentDevice = function () {
        var breakpoints = {mobile: 320, tablet: 768, desktop: 1000};
           var breakpoint = false;
        for(var key in breakpoints) {

            if (breakpoints[key] < document.documentElement.clientWidth) {
                breakpoint = key;
            }
        }
           return breakpoint;
       },
       getSmartListPos = function (recorded_positions) {
           if(recorded_positions !== undefined && recorded_positions.length > 0)
           {
               var currentDevice = getCurrentDevice(), formats = [];

               for(var i in recorded_positions) {
                   var position = recorded_positions[i];
                   var breakpoints = position[4] ? position[4].split(" ") : false;
                   if (position[1] !== undefined && (breakpoints === false || breakpoints.indexOf(currentDevice) > -1)) {
                       formats.push(position[1]);
                   }
               }

               return formats.join(",");
           }
           return global.lmd.context.page.advert.smart.all_formats;
       },
       getSmartTarget = function () {
          var user_type = getUserType(),
              rubriques = getElementRubriques(),
              item_id = getElementId(),
              article_has_atome_video = articleHasAtomeVideo(),
              article_is_longform = articleIsLongform(),
              article_type = articleType(),
              target = [],
              referrer_domain;

          if (item_id) {
             target.push("item_id=" + item_id);
          }
          if (user_type) {
             target.push("user=" + user_type);
          }
          target.push("articlevideo=" + article_has_atome_video);
          target.push("longform=" + article_is_longform);
          target.push("articletype=" + article_type);

          if (document.referrer) {
             /* recuperation sioux du hostname du referrer */
             referrer_domain = (function(url) {
                var a = document.createElement('a');
                a.href = url;
                return a.hostname;
             })(document.referrer);

             target.push("referrer-domain=" + referrer_domain);
          }

          rubriques = rubriques.map(function (rub){
             return "rub=" + rub;
          });

          target = target.concat(rubriques);

          return target.join(";");
       },
       getSmartPageId = function () {
           var siteId = global.lmd.context.page.advert.smart.site,
               pageId = global.lmd.context.page.advert.smart.page;
           return siteId + '/' + pageId;
       },
       handleSmart = function (global, SMART_listpos_temp) {
           var sas_formatids,
               sas_target,
               sas_tmstp,
               sas_pageid;

           if (!isAdvertActive()) {
               global.ADVERT_AD = function () {
               };
               return;
           }

           /* callback lorsque pub est chargee */
           global.sas_loadHandler = function (f) {
               lmd.advertController.handleAd(f);
           };

           sas_tmstp = Math.round(Math.random() * 10000000000);
           sas_pageid = getSmartPageId();
           sas_formatids = getSmartListPos(SMART_listpos_temp);
           sas_target = getSmartTarget();

           /* variables globales car utilisees par smartadserver.js */
           global.sas_renderMode = global.lmd.context.page.advert.smart.render_mode || 0;
           global.sas_scriptDomain = 'http://' + global.lmd.context.page.advert.smart.domain;

           if (sas_formatids.length > 0) {
               require([global.sas_scriptDomain + '/call2/pubjallajax/' + sas_pageid + '/' + sas_formatids + '/' + sas_tmstp + '/' + escape(sas_target) + '?'], function() {
                   initFunction();
               });
           } else {
               initFunction();
           }

           /**
            * on redeclare nos propres fonctions de la librairie smart
            */
           declareSmartAdLib();

           // attention dans un cadre partenaires, on ne met pas OAS_AD à vide
           global.OAS_AD = (global.LMD_EXPORT && global.OAS_AD === global.LMD_EXPORT.Advert) ? global.OAS_AD : function (){};
           global.ADVERT_AD = function (params) {
               var sas_pageid = params[0].split('/'),
                   sas_formatid = params[1];

               /* ne pas construire la position si appel a la demande */
               if (global.lmd.context.page.advert.smart.render_mode !== 2) {
                   lmd.advertController.buildPositionAdvert([sas_pageid[1], sas_formatid]);
               }

           };

           /*
            * pour la fonctionnalité de live-preview de smartadserver, on affiche tous les blocs pub si le hostname est
            * chez eux
            */
           if (window.location.hostname.indexOf('smartadserver.com') >= 0) {
               (function() {
                   var pubs = document.querySelectorAll('[data-adpage="' + global.lmd.context.page.advert.smart.page + '"]'),
                       i;
                   if (pubs === null) {
                       return;
                   }
                   for(i = 0; i < pubs.length; i++) {
                       pubs[i].style.display = 'block';
                   }
               }());
           }
       },
   /*
    * pour pouvoir :
    *  * construire les positions pub directement au bon endroit dans la page
    *  * charger les pubs dans le carousel de rubriques en abonnés
    *  * charger la pub sans utiliser des iframes pour les portfolios et la position pub en oreille_droite
    *
    *  on a besoin de fonctions qui n'utilisent pas de document.write
    *  on se base sur les fonctions de smartad dans lesquelles les document.write sont expurgés
    *  le conteneur d'id sas_[formatid] est créé par nous via de la manipulation de DOM
    */
       declareSmartAdLib = function () {
         global.sas_urls = new Array();

         // modif
         global.SmartAdServer = function (c, a, b) {
            if (sas_mfb == 1) {
               sas_mfb = 0;
               sas_master = "M";
            } else {
               sas_master = "S";
            }
            var e = sas_gcf(a);

            var script = sas_d.createElement("script");
            script.src = sas_scriptDomain + "/call/pubj/" + c + "/" + a + "/" + sas_master + "/" + sas_tsn + "/" + escape(b) + "?";
            e.appendChild(script);
         };

         // modif
         global.SmartAdServerAjax = function (h, c, f, g) {
            if (typeof(this.sas_pageid) == "undefined") {
               this.sas_pageid = h;
            }
            var e = sas_gcf(c);
            if (sas_mfb == 1) {
               sas_mfb = 0;
               sas_master = "M";
            } else {
               sas_master = "S";
            }
            sas_scripturl = g || sas_scriptDomain + "/call/pubj/" + h + "/" + c + "/" + sas_master + "/" + sas_tsn + "/" + escape(f) + "?";

            // Dans notre cas, e est toujours défini, même avant le premier
            // appel à la fonction, du coup on discrimine par rapport à la
            // présence dans sas_fa.
            // if ((typeof(e) == "undefined") || (e == null)) {
            if (sas_fa.indexOf(c) < 0) {
               sas_fa.push(c);
               sas_ta.push(f);
               sas_urls.push(sas_scripturl);
               if (sas_renderMode == 0) {
                  // sas_d.write('<div id="sas_' + c + '"></div>');
                  var a = sas_createScript(c, sas_scripturl);
                  var d = sas_d.getElementById("sas_" + c);
                  d.appendChild(a);
               } else {
                  if (sas_renderMode == 3) {
                     // sas_d.write('<div id="sas_' + c + '"></div>');
                     var b = "sas_d.getElementById('sas_" + c + "').appendChild(sas_createScript(" + c + ", '" + sas_scripturl + "'));";
                     sas_w.setTimeout(b, sas_callIndex * sas_delay);
                     sas_callIndex++;
                  } else {
                     if (sas_renderMode == 4) {
                        // sas_d.write('<div id="sas_' + c + '"><script id="sas_s' + c + '" src="' + sas_scripturl + '"><\/script></div>')
                     } else {
                        // sas_d.write('<div id="sas_' + c + '"></div>');
                        if (sas_renderMode == 1 && !sas_olfb) {
                           sas_olfb = 1;
                           sas_addEvent(sas_w, "load", sas_callAds, false);
                        }
                     }
                  }
               }
            } else {
               var a = sas_createScript(c, sas_scripturl);
               sas_ccf(c);
               sas_appendToContainer(c, a);
            }
         };

         // modif
         global.SmartAdServerAjaxOneCall = function (h, c, g) {
            if (typeof(this.sas_pageid) == "undefined") {
               this.sas_pageid = h;
            }
            if (sas_mfb == 1) {
               sas_mfb = 0;
               sas_master = "M";
            } else {
               sas_master = "S";
            }
            sas_fa.push(c);
            sas_ta.push(g);

            if (typeof(sas_manager) != "undefined") {
               if (sas_manager.exists(c)) {
                  var d = sas_manager.formats["f" + c].scriptSrc();
                  var b = sas_manager.formats["f" + c].scriptType();
                  var a = 0;
                  var f = 0;
                  if (b == "iframe") {
                     a = sas_manager.formats["f" + c].scriptWidth();
                     f = sas_manager.formats["f" + c].scriptHeight();
                  }
                  sas_render(c, d, b, a, f);
               } else {
                  sas_unrenderedFormats.push(c);
               }
            } else {
               sas_unrenderedFormats.push(c);
            }
         };


         if (typeof(sas_scriptDomain) == "undefined") {
            global.sas_scriptDomain = "http://www.smartadserver.com";
         }
         if (typeof(sas_renderMode) == "undefined") {
            global.sas_renderMode = 0;
         }
         global.sas_ajax = true;
         global.sas_callIndex = 1;
         global.sas_delay = 20;
         global.sas_d = document;
         global.sas_w = window;
         global.sas_gtsf = function () {
            return Math.round(Math.random() * 10000000000);
         };
         global.sas_tsn = sas_gtsf();
         global.sas_mfb = 1;
         global.sas_olfb = 0;
         global.sas_fa = new Array();
         global.sas_ta = new Array();
         global.sas_aca = new Array();
         global.sas_ccba = new Array();
         if (typeof(sas_unrenderedFormats) == "undefined") {
            global.sas_unrenderedFormats = new Array();
         }
         global.icb = navigator.userAgent.toLowerCase().indexOf("chrome") > -1;
         global.arrayIndex = function (a, b) {
            for (var c = 0; c < a.length; c++) {
               if (a[c] == b) {
                  return c;
               }
            }
            return -1;
         };
         global.sas_ccf = function (c) {
            var b = sas_gcf(c);
            myLength = b.childNodes.length;
            if ((b.childNodes != null) && (myLength > 0)) {
               for (sas_cccn = 0; sas_cccn < myLength; sas_cccn++) {
                  b.removeChild(b.childNodes[0]);
               }
            }
            if (sas_aca.length >= c) {
               if ((typeof(sas_aca[c]) != "undefined") && (sas_aca[c] != null)) {
                  for (sas_aca_counter = 0; sas_aca_counter < sas_aca[c].length; sas_aca_counter++) {
                     var a = sas_aca[c][sas_aca_counter];
                     if ((typeof(a) != "undefined") && (a != null)) {
                        a.parentNode.removeChild(a);
                     }
                  }
                  sas_aca[c] = new Array()
               }
            }
            if (sas_ccba.length >= c) {
               if (typeof(sas_ccba[c]) == "function") {
                  sas_ccba[c]();
                  sas_ccba[c] = null;
               }
            }
         };
         global.sas_gcf = function (a) {
            return sas_d.getElementById("sas_" + a);
         };
         global.sas_appendToContainer = function (c, a) {
            var d = sas_gcf(c);
            if ((typeof(d) != "undefined") && (d != null) && (typeof(a) != "undefined") && (a != null)) {
               if (typeof(a) == "string") {
                  var b = sas_d.createElement("div");
                  b.innerHTML = a;
                  a = b;
               }
               d.appendChild(a);
               if (icb) {
                  d.style.visibility = "hidden";
                  sas_w.setTimeout(function () {
                     sas_fv(c);
                  }, 100);
               }
            }
         };
         global.sas_appendScripts = function (a, b) {
            if (typeof (b) != "undefined") {
               for (i = 0; i < b.length; i++) {
                  sas_appendToContainer(a, b[i]);
               }
            }
         };
         global.sas_fv = function (a) {
            var b = sas_gcf(a);
            if ((typeof(b) != "undefined") && (b != null)) {
               b.style.visibility = "visible";
            }
         };
         global.sas_addCleanListener = function (b, a) {
            sas_ccba[b] = a;
         };

         global.sas_render = function (d, f, b, a, g) {
            if (sas_renderMode == 0) {
               var c;
               if (b == "iframe") {
                  c = sas_createIframe(d, f, a, g);
               } else {
                  c = sas_createScript(d, f);
               }
               var e = sas_d.getElementById("sas_" + d);
               e.appendChild(c);
            } else {
               var h = arrayIndex(sas_fa, d);
               if (h >= 0 && !sas_urls[h]) {
                  sas_urls[h] = f;
               }
               if (sas_renderMode == 1 && !sas_olfb) {
                  sas_olfb = 1;
                  sas_addEvent(sas_w, "load", sas_callAds, false);
               }
            }
         };
         global.sas_createIframe = function (c, d, a, e) {
            var b = sas_d.createElement("iframe");
            b.id = "sas_i" + c;
            b.src = d;
            b.setAttribute("width", a);
            b.setAttribute("height", e);
            b.frameBorder = "0";
            b.style.border = 0;
            b.scrolling = "no";
            b.marginWidth = "0px";
            b.marginHeight = "0px";
            b.setAttribute("vspace", 0);
            b.setAttribute("hspace", 0);
            b.setAttribute("allowtransparency", true);
            return b;
         };
         global.sas_createScript = function (b, c) {
            var a = sas_d.createElement("script");
            a.id = "sas_s" + b;
            a.type = "text/javascript";
            a.src = c;
            a.onreadystatechange = function () {
               if (this.readyState == "loaded") {
                  sas_scriptLoadHandler(this);
               }
            };
            if ((window.opera === undefined) && ((navigator.appVersion.indexOf("MSIE 9") < 0))) {
               a.onload = sas_scriptLoadHandler;
            }
            a.async = "async";
            return a;
         };
         global.sas_scriptLoadHandler = function (c) {
            var d;
            if (c.id !== undefined) {
               d = c.id.replace("sas_s", "");
            } else {
               if (c.target !== undefined && c.target.id !== undefined) {
                  d = c.target.id.replace("sas_s", "");
               }
            }
            if (d != null && typeof(sas_loadHandler) != "undefined") {
               var b = sas_gcf(d);
               var a = {id: d};
               if (b != null && b.hasChildNodes() && b.childNodes.length > 1) {
                  a.hasAd = true;
               } else {
                  a.hasAd = false;
               }
               sas_loadHandler(a);
            }
         };
         global.sas_callAds = function () {
            sas_callIndex = 1;
            if (sas_fa.length > 0) {
               sas_tsn = sas_gtsf();
               sas_mfb = 1;
               for (var a = 0; a < sas_fa.length; a++) {
                  SmartAdServerAjax(sas_pageid, sas_fa[a], sas_ta[a], sas_urls[a]);
               }
            }
         };
         global.sas_callAd = function (d, e, b, a) {
            if (b === undefined) {
               b = true;
            }
            if (a === undefined) {
               a = true;
            }
            if (b) {
               sas_mfb = 1;
            }
            if (a) {
               sas_tsn = sas_gtsf();
            }
            for (var c = 0; c < sas_fa.length; c++) {
               if (d == sas_fa[c]) {
                  sas_target = sas_ta[c];
                  if (typeof(e) != "undefined") {
                     sas_target = e;
                  }
                  SmartAdServerAjax(sas_pageid, sas_fa[c], sas_target);
               }
            }
         };
         global.sas_cleanAds = function () {
            if (sas_fa.length > 0) {
               for (var a = 0; a < sas_fa.length; a++) {
                  sas_ccf(sas_fa[a]);
               }
            }
         };
         global.sas_cleanAd = function (a) {
            for (i = 0; i < sas_fa.length; i++) {
               if (a == sas_fa[i]) {
                  sas_ccf(sas_fa[i]);
               }
            }
         };
         global.SmartAjaxRender = function (a, b) {
            if ("object" == typeof(a.formats["f" + b])) {
               if (a.formats["f" + b].scriptType() == "iframe") {
                  iframe = sas_d.createElement("iframe");
                  iframe.setAttribute("width", a.formats["f" + b].scriptWidth());
                  iframe.setAttribute("height", a.formats["f" + b].scriptHeight());
                  iframe.marginWidth = "0px";
                  iframe.marginHeight = "0px";
                  iframe.setAttribute("vspace", 0);
                  iframe.setAttribute("hspace", 0);
                  iframe.scrolling = "no";
                  iframe.setAttribute("frameborder", 0);
                  iframe.setAttribute("allowtransparency", true);
                  iframe.setAttribute("src", a.formats["f" + b].scriptSrc());
                  sas_appendToContainer(b, iframe);
               } else {
                  sas_script = sas_d.createElement("script");
                  sas_script.setAttribute("src", a.formats["f" + b].scriptSrc());
                  sas_appendToContainer(b, sas_script);
               }
            }
         };
         global.SmartAdServerOCAjax = function (d, a, c) {
            var b = sas_gcf(a);
            if (sas_mfb == 1) {
               sas_mfb = 0;
               sas_master = "M";
            } else {
               sas_master = "S";
            }
            if ((typeof(b) == "undefined") || (b == null)) {
               sas_fa.push(a);
               sas_ta.push(c);
               sas_d.write('<div id="sas_' + a + '"></div>');
            } else {
               if (typeof sas_manager != "undefined") {
                  SmartAjaxRender(sas_manager, a);
               }
            }
         };
         global.getAjaxOCUrl = function () {
            for (var a = 0; a < document.scripts.length; a++) {
               var b = document.scripts[a];
               if (b.src && b.src.indexOf("pubjallajax") > 0) {
                  return b.src;
               }
            }
            return "";
         };
         global.generateAjaxOCRefreshUrl = function (a, b) {
            if (!a) {
               a = getAjaxOCUrl();
            }
            var c = a.split("/");
            c[8] = b;
            return c.join("/");
         };
         global.sas_callAdsOC = function () {
            if (sas_fa.length > 0) {
               var a = sas_tsn;
               sas_tsn = sas_gtsf();
               sas_mfb = 1;
               sas_cleanAds();
               var c = "";
               var b = sas_d.getElementById("sas_oc_" + a);
               if (b) {
                  c = b.src;
                  b.parentElement.removeChild(b);
               }
               b = sas_d.createElement("script");
               b.id = "sas_oc_" + sas_tsn;
               b.type = "text/javascript";
               b.src = generateAjaxOCRefreshUrl(c, sas_tsn);
               sas_d.head.appendChild(b);
            }
         };
         global.sas_addEvent = function (e, b, c, a) {
            if (e.addEventListener) {
               e.addEventListener(b, c, a);
               return true;
            } else {
               if (e.attachEvent) {
                  var d = e.attachEvent("on" + b, c);
                  return d
               } else {
                  e["on" + b] = c;
               }
            }
            return true;
         };
       };

   handleSmart(global, smart_recorded_positions);
}(typeof SMART_listpos_temp === "undefined" ? undefined : SMART_listpos_temp, typeof SMART_init !== "function" ? undefined: SMART_init));
