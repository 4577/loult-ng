﻿document.addEventListener('DOMContentLoaded', function() {
	var audio = (window.AudioContext || typeof webkitAudioContext !== 'undefined');
	var userlist = document.getElementById('userlist');
	var underlay = document.getElementById('underlay');
	var usertbl = document.getElementById('usertbl');
	var chatbox = document.getElementById('chatbox');
	var chattbl = document.getElementById('chattbl');
	var input = document.getElementById('input');
	var theme = localStorage.theme || 'day';
	var left = (localStorage.left === 'true');
	var dt = (localStorage.dt === 'true');
	var hr = (localStorage.hr === 'true');
	var waitTime = 1000;
	var users = {};
	var muted = [];
	var you = null;
	var lastMsg;
	var lastId;
	var lastTd;
	var ws;

	// DOM-related functions

	var parser = function(raw_msg) {
		var rules = [
			{
				test: msg => msg.includes('http'),
				run: msg => msg.replace(/https?:\/\/[^< ]*[^<*.,?! :]/g, '<a href="$&" target="_blank">$&</a>'),
			},
			{
				test: msg => msg.includes('**'),
				run: msg => msg.replace(/\*{2}([^\*]+)\*{2}?/gu, '<span class="spoiler">$1</span>'),
			},
			{
				test: msg => msg.includes('://vocaroo.com/i/'),
				run: msg => msg.replace(/<a href="https?:\/\/vocaroo.com\/i\/(\w+)" target="_blank">https?:\/\/vocaroo.com\/i\/\w+<\/a>/g, '<audio controls><source src="http://vocaroo.com/media_command.php?media=$1&command=download_mp3" type="audio/mpeg"><source src="http://vocaroo.com/media_command.php?media=$1&command=download_webm" type="audio/webm"></audio>$&'),
			},
			{
				test: msg => msg.startsWith('&gt;'),
				run: msg => msg.replace(/(.+)/g, '<span class="greentext">$1</span>'),
			}
		];

		var tests = rules.filter(rule => ('test' in rule) && rule.test(raw_msg));
		return tests.filter(rule => 'run' in rule).reduce((prev, rule) => rule.run(prev), raw_msg);;
	};

	var addLine = function(pkmn, txt, datemsg, trclass, uid) {
		var uid = uid || null;
		var trclass = trclass || [];
		var tr = document.createElement('tr');
		var td = document.createElement('td');
		var trclass = trclass || [];
		var uid = uid || null;
		var parsed = txt;

		if(pkmn.color) {
			parsed = parser(txt);
			tr.style.color = pkmn.color;
		}

		if(pkmn === 'info' || trclass.indexOf('me') > -1) {
			var i = document.createElement('i');
			i.className = 'material-icons';
			i.appendChild(document.createTextNode('info_outline'));
			td.appendChild(i);
			tr.appendChild(td);
			lastTd = td;
		}
		else if(lastId !== uid || lastTd.getElementsByTagName('i').length > 0) {
			var label = document.createElement('label');
			label.appendChild(document.createTextNode(pkmn.name));
			label.style.backgroundImage = 'url("/pokemon/' + pkmn.img + '.gif")';
			td.style.backgroundImage = 'url("/img/pokemon/' + pkmn.img + '.gif")';
			label.className = (left ? 'left' : 'right');
			td.appendChild(label);
			tr.appendChild(td);
			lastTd = td;
		}
		else {
			lastTd.rowSpan = ++lastTd.rowSpan;
			trclass.push('merged');
		}

		lastId = uid;

		if(trclass.indexOf('me') > -1)
			parsed = 'Le ' + pkmn.name + ' sauvage ' + parsed;

		td = document.createElement('td');
		td.innerHTML = parsed;
		tr.appendChild(td);

		td = document.createElement('td');
		var sp = document.createElement('span');
		if(dt)
			sp.className = 'show';
		sp.appendChild(document.createTextNode((new Date(datemsg)).toLocaleDateString()));
		td.appendChild(sp);

		sp = document.createElement('span');
		if(dt && hr)
			sp.className = 'show';
		sp.appendChild(document.createTextNode(' '));
		td.appendChild(sp);

		sp = document.createElement('span');
		if(hr)
			sp.className = 'show';
		sp.appendChild(document.createTextNode((new Date(datemsg)).toLocaleTimeString()));
		td.appendChild(sp);
		tr.appendChild(td);
		tr.className = trclass.join(' ');

		var atBottom = (chatbox.scrollTop === (chatbox.scrollHeight - chatbox.offsetHeight));
		chattbl.appendChild(tr);
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	};

	var addUser = function(userid, params) {
		if(userid in users)
			return;

		users[userid] = params;
		
		if(ambtn.checked && muted.indexOf(userid) === -1)
			muted.push(userid);
		
		var tr = document.createElement('tr');
		var td = document.createElement('td');
		var label = document.createElement('label');
		label.appendChild(document.createTextNode(params.name));
		label.style.color = params.color;
		label.style.backgroundImage = 'url("/pokemon/' + params.img + '.gif")';
		label.className = 'left';
		td.appendChild(label);
		tr.appendChild(td);
		td = document.createElement('td');

		if(!params.you) {
			var sound = document.createElement('div');
			var i = document.createElement('i');
			sound.className = 'btn';
			i.className = 'material-icons';
			i.appendChild(document.createTextNode('volume_' + (muted.indexOf(userid) != -1 ? 'off' : 'up')));
			sound.appendChild(i);
			td.appendChild(sound);

			sound.onmousedown = function() {
				var mt = (muted.indexOf(userid) != -1);
				if(!mt) {
					muted.push(userid);
					i.innerHTML = 'volume_off';
				}
				else {
					muted.splice(muted.indexOf(userid), 1);
					i.innerHTML = 'volume_up';
				}
			};
		}
		else {
			underlay.style.backgroundImage = 'url("/dev/pokemon/' + params.img + '.png")';
			you = userid;
		}

		tr.appendChild(td);
		usertbl.appendChild(tr);
		users[userid].dom = tr;
	};

	var delUser = function(userid) {
		usertbl.removeChild(users[userid].dom);
		delete users[userid];
	};

	// Preferences

	var gear = document.getElementById('gear');
	var overlay = document.getElementById('overlay');
	var cover = document.getElementById('cover');
	var close = document.getElementById('close');
	var rightbtn = document.getElementById('right');
	var leftbtn = document.getElementById('left');
	var themes = document.getElementById('theme');
	var ambtn = document.getElementById('am');
	var dtbtn = document.getElementById('dt');
	var hrbtn = document.getElementById('hr');
	var head = document.getElementById('head');
	var main = document.getElementById('main');

	var openWindow = function() {
		overlay.style.display = 'block';
		head.className = main.className = 'blur-in';
	};
	var closeWindow = function() {
		overlay.style.display = 'none';
		head.className = main.className = '';
	};

	gear.onclick = openWindow;
	cover.onclick = closeWindow;
	close.onclick = closeWindow;

	rightbtn.checked = !left;
	leftbtn.checked = left;
	var align = function(evt) {
		localStorage.left = left = !rightbtn.checked;
		var rows = document.querySelectorAll('#chattbl td:first-child label');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (left ? 'left' : 'right');
	};
	rightbtn.onclick = leftbtn.onclick = align;

	dtbtn.checked = dt;
	dtbtn.onchange = function(evt) {
		localStorage.dt = dt = dtbtn.checked;
		var atBottom = (chatbox.scrollTop === (chatbox.scrollHeight - chatbox.offsetHeight));
		var rows = document.querySelectorAll('#chattbl td:last-child span:first-child');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (dt ? 'show' : '');
		mid(atBottom);
	};

	hrbtn.checked = hr;
	hrbtn.onchange = function(evt) {
		localStorage.hr = hr = hrbtn.checked;
		var atBottom = (chatbox.scrollTop === (chatbox.scrollHeight - chatbox.offsetHeight));
		var rows = document.querySelectorAll('#chattbl td:last-child span:last-child');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = (hr ? 'show' : '');
		mid(atBottom);
	};

	var mid = function(atBottom) {
		var rows = document.querySelectorAll('#chattbl td:last-child span:nth-child(2)');
		for(var i = 0; i < rows.length; i++)
			rows[i].className = ((dt && hr) ? 'show' : '');
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	};

	document.body.className = themes.value = theme;

	themes.onchange = function() {
		localStorage.theme = theme = this.value;
		document.body.className = theme;
		chatbox.scrollTop = chatbox.scrollHeight;
	};

	// Languages

	var select = document.getElementById('lang');
	var lang = document.cookie.match(/lang=(\w{2})/);

	if(!lang) {
		var l = navigator.language.substr(0, 2);
		switch(l) {
			case 'fr':
			case 'es':
			case 'de':
				lang = l;
			break;
			default:
				lang = 'en';
		}
		document.cookie = 'lang=' + lang + '; Path=/';
	}
	else
		lang = lang[1];

	select.value = lang;

	select.onchange = function() {
		lang = this.value;
		document.cookie = 'lang=' + lang + '; Path=/';
	};

	// Focus-related functions

	var dontFocus = false;

	select.addEventListener('focus', function() {
		dontFocus = true;
	}, false);

	themes.addEventListener('focus', function() {
		dontFocus = true;
	}, false);

	var refocus = function(evt) {
		setTimeout(function() {
			if(!dontFocus && !window.getSelection().toString())
				input.focus();
			else if(dontFocus)
				dontFocus = false;
		}, 10);
	};

	window.addEventListener('focus', refocus, false);
	document.body.addEventListener('mouseup', refocus, false);

	window.addEventListener('resize', function(evt) {
		chatbox.scrollTop = chatbox.scrollHeight;
	});

	// Sound and volume

	if(audio)
	{
		var vol = document.getElementById('vol');
		var speaker = document.getElementById('speaker');
		var volrange = document.getElementById('volrange');
		var context = new (window.AudioContext || webkitAudioContext)();
		var volume = (context.createGain ? context.createGain() : context.createGainNode());
		volume.connect(context.destination);

		var changeVolume = function() {
			localStorage.volume = volume.gain.value = volrange.value * 0.01;
			changeIcon(volrange.value);
		};

		var changeIcon = function(v) {
			vol.innerHTML = (v > 0 ? (v > 50 ? 'volume_up' : 'volume_down') : 'volume_mute');
		};

		if(localStorage.volume) {
			volrange.value = localStorage.volume * 100;
			volume.gain.value = localStorage.volume;
			changeIcon(volrange.value);
		}

		speaker.onclick = function() {
			volume.gain.value = (volume.gain.value > 0 ? 0 : volrange.value * 0.01);
			changeIcon(volume.gain.value * 100);
		};

		volrange.oninput = changeVolume;
	}

	// Speech

	if('webkitSpeechRecognition' in window) {
		var recognition = new webkitSpeechRecognition();
		var recognizing = false;

		var chatentry = document.getElementById('chatentry');
		var div = document.createElement('div');
		var i = document.createElement('i');
		div.className = 'btn';
		i.className = 'material-icons';
		i.appendChild(document.createTextNode('mic_none'));
		div.appendChild(i);
		chatentry.appendChild(div);
		div.onclick = function () {
			if(recognizing) {
				recognition.stop();
				i.innerHTML = 'mic_off';
				return;
			}
			i.innerHTML = 'mic';
			recognition.lang = lang + '-' + ((lang === 'en') ? 'US' : lang.toUpperCase());
			recognition.start();
			input.value = '';
		};

		recognition.continuous = true;
		recognition.interimResults = true;

		recognition.onstart = function() {
			recognizing = true;
		};

		recognition.onerror = function(event) {
			// console.log(event.error);
		};

		recognition.onend = function() {
			recognizing = false;
		};

		recognition.onresult = function(event) {
			var interim_transcript = '';
			for(var i = event.resultIndex; i < event.results.length; i++)
				if(event.results[i].isFinal) {
					var m = input.value.trim();
					if(m.length) {
						ws.send(JSON.stringify({type: 'msg', msg: m, lang: lang}));
						lastMsg = input.value;
						input.value = '';
					}
				}
				else
					interim_transcript += event.results[i][0].transcript;

			input.value = interim_transcript.trim();
			input.value = input.value.charAt(0).toUpperCase() + input.value.slice(1);
		};
	}

	// Users list display

	var userswitch = document.getElementById('userswitch');

	userswitch.onclick = function() {
		var atBottom = (chatbox.scrollTop === (chatbox.scrollHeight - chatbox.offsetHeight));
		userlist.style.width = (userlist.style.width === '0px' ? '185px' : '0px');
		underlay.style.right = userlist.style.width;
		if(atBottom)
			chatbox.scrollTop = chatbox.scrollHeight;
	};

	// WebSocket-related functions

	var wsConnect = function() {
		ws = new WebSocket(location.origin.replace('http', 'ws') + '/socket' + location.pathname);
		// ws = new WebSocket('wss://loult.family/socket/' + location.pathname);
		ws.binaryType = 'arraybuffer';

		var lastMuted = false;

		input.onkeydown = function(evt) {
			underlay.className = '';
			if(evt.keyCode === 13 && input.value) {
				var trimed = input.value.trim();
				if(trimed.charAt(0) === '/') {
					if(trimed.match(/^\/atta(ck|que)\s/i)) {
						var splitted = trimed.split(' ');
						ws.send(JSON.stringify({ type : 'attack', target : splitted[1], order : ((splitted.length === 3) ? parseInt(splitted[2]) : 0) }));
					}
					else if(trimed.match(/^\/(en|es|fr|de)\s/i)) {
						ws.send(JSON.stringify({type: 'msg', msg: trimed.substr(4), lang: trimed.substr(1, 2).toLowerCase()}));
						underlay.className = 'pulse';
					}
					else if(trimed.match(/^\/vol(ume)?\s(100|\d{1,2})$/i) && audio) {
						volrange.value = trimed.match(/\d+$/i)[0];
						changeVolume();
					}
					else if(trimed.match(/^\/(help|aide)$/i)) {
						var d = new Date;
						addLine('info', "/attaque, /attack : Lancer une attaque sur quelqu'un. Exemple : /attaque Miaouss", d, ['part']);
						addLine('info', "/en, /es, /fr, /de : Envoyer un message dans une autre langue. Exemple : /en Where is Pete Ravi?", d, ['part']);
						if(audio)
							addLine('info', "/volume, /vol : Régler le volume rapidement. Exemple : /volume 50", d, ['part']);
						addLine('info', "/me : Réaliser une action. Exemple: /me essaie la commande /me.", d, ['part']);
						addLine('info', "> : Indique une citation. Exemple : >Je ne reviendrais plus ici !", d, ['part']);
						addLine('info', "** ** : Masquer une partie d'un message. Exemple : Carapuce est un **chic type** !", d, ['part']);
					}
					else if(trimed.match(/^\/me\s/i))
						ws.send(JSON.stringify({type: 'me', msg: trimed.substr(4)}));
					else {
						ws.send(JSON.stringify({type: 'msg', msg: trimed, lang: lang}));
						underlay.className = 'pulse';
					}
				}
				else if(trimed.length) {
					ws.send(JSON.stringify({type: 'msg', msg: trimed, lang: lang}));
					underlay.className = 'pulse';
				}

				lastMsg = input.value;
				input.value = '';
			}
			else if(evt.keyCode === 38 || evt.keyCode === 40) {
				evt.preventDefault();
				input.value = (lastMsg && !input.value ? lastMsg : '');
			}
		};

		ws.onopen = function() {
			waitTime = 1000;
		};

		ws.onmessage = function(msg) {
			if(typeof msg.data === 'string') {
				msg = JSON.parse(msg.data);
				lastMuted = (muted.indexOf(msg.userid) != -1);

				switch(msg.type) {
					case 'msg':
					case 'me':
					case 'bot':
						if(!lastMuted)
							addLine(users[msg.userid], msg.msg, msg.date, [msg.type], msg.userid);
					break;

					case 'connect':
						if(!lastMuted)
							addLine('info', 'Un ' + msg.params.name + ' sauvage apparaît !', msg.date, ['log']);
						addUser(msg.userid, msg.params);
					break;

					case 'disconnect':
						if(!lastMuted)
							addLine('info', 'Le ' + users[msg.userid].name + " sauvage s'enfuit !", msg.date, ['log', 'part']);
						delUser(msg.userid);
					break;

					case 'attack':
						switch(msg['event']) {
							case 'attack':
								addLine('info', users[msg.attacker_id].name + ' attaque ' + users[msg.defender_id].name + ' !', msg.date, ['log']);
							break;
							case 'dice':
								addLine('info', users[msg.attacker_id].name + ' tire un ' + msg.attacker_dice + ' + ('+ msg.attacker_bonus + '), ' + users[msg.defender_id].name + ' tire un ' + msg.defender_dice + ' + (' + msg.defender_bonus + ') !', msg.date, ['log']);
							break;
							case 'effect':
								addLine('info', users[msg.target_id].name + " est maintenant affecté par l'effet " + msg.effect + ' !', msg.date, ['log']);
								if(msg.target_id === you)
								{
									var d = new Date(msg.date);
									d.setSeconds(d.getSeconds() + msg.timeout);
									setTimeout(function() { addLine('info', "L'effet " + msg.effect + ' est terminé.', d, ['log', 'part']); }, msg.timeout * 1000);
								}
							break;
							case 'invalid':
								addLine('info', "Impossible d'attaquer pour le moment, ou pokémon invalide", msg.date, ['log', 'kick']);
							break;
							case 'nothing':
								addLine('info', 'Il ne se passe rien...', msg.date, ['log', 'part']);
							break;
						}
					break;

					case 'antiflood':
						switch(msg['event']) {
							case 'banned':
								addLine('info', users[msg.flooder_id].name + ' est un sale flooder. Il a été banni temporairement.', msg.date, ['log', 'kick']);
							break;
							case 'flood_warning':
								addLine('info', 'Attention, vous avez été détecté comme flooder. Dernier avertissement.', msg.date, ['log', 'kick']);
							break;
						}
					break;

					case 'userlist':
						for(var i = 0; i < msg.users.length; i++)
							addUser(msg.users[i].userid, msg.users[i].params);
					break;

					case 'backlog':
						for(var i = 0; i < msg.msgs.length; i++)
							addLine(msg.msgs[i].user, msg.msgs[i].msg, msg.msgs[i].date, ['backlog', msg.msgs[i].type], msg.msgs[i].userid);
						addLine('info', 'Vous êtes connecté.', (new Date), ['log']);
					break;
				}
			}
			else if(!lastMuted && audio && volume.gain.value > 0) {
				context.decodeAudioData(msg.data, function(buf) {
					var source = context.createBufferSource();
					source.buffer = buf;
					source.connect(volume);
					source.start();
				});
			}
		};

		ws.onerror = function(e) {
			console.log(['error', e]);
		};

		ws.onclose = function() {
			for(var i in users)
				delUser(i);

			addLine('info', 'Vous êtes déconnecté, réessai...', (new Date), ['log', 'part']);

			window.setTimeout(wsConnect, waitTime);
			waitTime = Math.min(waitTime * 2, 120000);
		};
	};

	wsConnect();
});
