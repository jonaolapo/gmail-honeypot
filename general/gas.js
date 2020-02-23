/** Google Apps Script for honey accounts 
 * Author: Jeremiah Onaolapo 2016
 * 
 * Change the value of SAFEHOUSE variable inside ScanEmails() and sendHeartbeatMsg() functions (to the notification store email address). 
 * Embed this script in honey accounts to monitor activity in them. It will send activity notifications to SAFEHOUSE. 
 * **/
 
function Install() {
  
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  
  Uninstall();  
  ScanEmails();  
  
  ScriptApp.newTrigger("ScanEmails").timeBased().everyHours(1).create();
  ScriptApp.newTrigger("sendHeartbeatMsg").timeBased().atHour(18).nearMinute(20).everyDays(1).create();
  
  Browser.msgBox("Success", "Installation successful", Browser.Buttons.OK);
}


function onOpen() {  
  var menu = [ 
    {name: "1: Init", functionName: "Init"},
    {name: "2: Install", functionName: "Install"},
    {name: "Uninstall", functionName: "Uninstall"}
  ];
  
  var mySheet = SpreadsheetApp.getActiveSpreadsheet();
  mySheet.addMenu(".", menu);
}


function Init() {
  Uninstall();
  Install();
}


function Uninstall() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
}


function ScanEmails() {
  // Flags - Locations
  const isinbox = '__ISINBOX__';
  const issent = '__ISSENT__';
  const isdraft = '__ISDRAFT__';
  const isspam = '__ISSPAM__';
  
  // Flags - States
  const istrash = '__ISTRASH__';
  const isread = '__ISREAD__';
  const isstarred = '__ISSTARRED__';
  const isrecent = '__ISRECENT__'
  
  var SAFEHOUSE = "notification-store@someservice.com";
  
  
  var thread, subject, mailid, body, from, 
      date, html, inboxemails, sentemails, draftemails, 
      spamemails, suspectemails = [], color, index = [], i;
  
  var sentmarker, draftmarker, spammarker;
  // Get marker values from Property Store
  ///
  ///
  ///
  
  var flags = [];
  //var vectorofflags = [];

  // CASE 1: Inbox mails %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  var inboxemails = GmailApp.getInboxThreads();
  var totalinboxcount = inboxemails.length;
  
  var readindex = [];   
  for (i=0; i<totalinboxcount; i++) {
    if(!inboxemails[i].isUnread() || inboxemails[i].hasStarredMessages()) {
      
      //flags.push(inboxemails[i].getId());
      
      if (!inboxemails[i].isUnread()) {
        flags.push(isread);
        suspectemails.push(inboxemails[i]);
        readindex.push(i);
        inboxemails[i].markUnread();
      }
      
      if(inboxemails[i].hasStarredMessages()) {
        flags.push(isstarred);
        suspectemails.push(inboxemails[i]);
        GmailApp.unstarMessages(inboxemails[i].getMessages());
        readindex.push(i);
      }
    }
  }
  
  html  = "<div style='max-width: 600px; width:100%'><p style='font-size:15px'>There are <strong>";
  html += suspectemails.length + "</strong> tampered messages in your inbox, as listed below: </p>";
  
  for (i=0; i<suspectemails.length; i++) {
    var n = readindex[i];
    var flgstr = flags[i];
    if (inboxemails[n]) {
      
      thread    = inboxemails[n].getMessages()[0];
      
      subject   = thread.getSubject();
      body      = thread.getRawContent();
      mailid      = thread.getId();
      from      = thread.getFrom();
      date      = Utilities.formatDate(thread.getDate(), Session.getTimeZone(), "MMM dd, yyyy"); //NB: getTimeZone() is deprecated
      
      if (i%2 == 0) color = "#f0f0f0"; else color = "#f9f9f9";
      
      html += "<p name='body' style='padding:15px;background-color:" + color + ";margin-bottom: 15px;'>";
      html += "<p name='flags' style='font-size:12px'>***BEGINFLAG*** " + flgstr + " ***ENDFLAG***" + " MAILID: " + mailid + "</p>";
      html += "<p name='subject' style='font-size:12px'>SUBJECT: " + subject + "</p>"
      html += "<span style='font-size:12px'>" + body;
      html += "</span></p>";
    }
  }
  
  //* Exfiltration
  if (suspectemails.length > 0) {
    tstamp = new Date();
    tstamp = tstamp.getTime();
    report = Utilities.newBlob(html, MimeType.PLAIN_TEXT, "report_" + tstamp + "_" + Math.random() + ".txt");
    GmailApp.sendEmail(SAFEHOUSE, "There are " + suspectemails.length + " tampered messages!", "Please find attached.", {attachments: [report]});
  }
  //*/
  // Delete sent emails to cover our exfiltration
  coverTracks(SAFEHOUSE);
  
  
  // CASE 2: Sent mails %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  flags = [];
  suspectemails = [];
  var properties = PropertiesService.getUserProperties();
  var sentmarker = new Date(properties.getProperty('sentmarker'));
  Logger.log('Stored sentmarker is: %s', properties.getProperty('sentmarker'));
  //var lastsent;
  if (!sentmarker)
    sentmarker = new Date("January 1, 1980 11:00:00"); // very old date
  var sthreads = GmailApp.search("in:Sent"); // after:" + dateString);
  Logger.log('Found %s sent threads', sthreads.length);
  
  //var label = GmailApp.createLabel("revisit");
  var newersdate = sentmarker;
  for (var i = 0; i < sthreads.length; i++) {
    var thread = sthreads[i];
    var z;
    for (z=0; z<thread.getMessages().length; z++) {
      var msgdate = thread.getMessages()[z].getDate();
      Logger.log('Current date/time of current message: %s', msgdate.toString());
      if (sentmarker < thread.getMessages()[z].getDate()) {
        // Also add a condition to exclude emails sent to SAFEHOUSE
        Logger.log("Current sender: %s", thread.getMessages()[z].getFrom());
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(issent);
        newersdate = thread.getMessages()[z].getDate();
        Logger.log('newersdate is now: ', newersdate);
      }
      if(thread.getMessages()[z].isStarred()) {
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(isstarred);
        recentmsg.unstar();
      }
    }
  }
  
  if(newersdate > sentmarker) sentmarker = newersdate;
  
  properties.setProperty('sentmarker', sentmarker.toString());
  Logger.log('New sentmarker is: %s', properties.getProperty('sentmarker'));
  
  html  = "<div style='max-width: 600px; width:100%'><p style='font-size:15px'>There are <strong>";
  html += suspectemails.length + "</strong> newly sent messages, as listed below: </p>";
  
  for (i=0; i<suspectemails.length; i++) {
    var flgstr = flags[i];
    if (true) {   
      subject   = suspectemails[i].getSubject();
      body      = suspectemails[i].getRawContent();
      mailid      = suspectemails[i].getId();
      from      = suspectemails[i].getFrom();
      date      = Utilities.formatDate(suspectemails[i].getDate(), Session.getTimeZone(), "MMM dd, yyyy"); //NB: getTimeZone() is deprecated
      
      if (i%2 == 0) color = "#f0f0f0"; else color = "#f9f9f9";
      
      html += "<p name='body' style='padding:15px;background-color:" + color + ";margin-bottom: 15px;'>";
      html += "<p name='flags' style='font-size:12px'>***BEGINFLAG*** " + flgstr + " ***ENDFLAG***" + " MAILID: " + mailid + "</p>"; // Include flags and mailid
      html += "<p name='subject' style='font-size:12px'>SUBJECT: " + subject + "</p>"
      html += "<span style='font-size:12px'>" + body;
      html += "</span></p>";
    }
  }
  
  Logger.log('No of suspected sent emails: %s', suspectemails.length);
  
  //* Exfiltration
  if (suspectemails.length > 0) {
    tstamp = new Date();
    tstamp = tstamp.getTime();
    report = Utilities.newBlob(html, MimeType.PLAIN_TEXT, "report_" + tstamp + "_" + Math.random() + ".txt");
    GmailApp.sendEmail(SAFEHOUSE, "There are " + suspectemails.length + " sent messages!", "Please find attached.", {attachments: [report]});
  //*/
  }
  // Delete sent emails to cover our exfiltration
  coverTracks(SAFEHOUSE);
  
  
  
  // CASE 3: Draft mails %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  flags = [];
  suspectemails = [];
  var properties = PropertiesService.getUserProperties();
  var dthreads = GmailApp.search("in:Drafts"); // after:" + dateString);
  Logger.log('Found %s draft threads', sthreads.length);
  
  //var newersdate = draftmarker;
  for (var i = 0; i < dthreads.length; i++) {
    var thread = dthreads[i];
    var z;
    for (z=0; z<thread.getMessages().length; z++) {
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(isdraft);
      if(thread.getMessages()[z].isStarred()) {
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(isstarred);
        recentmsg.unstar();
      }
    }
  }
  
  html  = "<div style='max-width: 600px; width:100%'><p style='font-size:15px'>There are <strong>";
  html += suspectemails.length + "</strong> draft messages, as listed below: </p>";
  
  for (i=0; i<suspectemails.length; i++) {
    var flgstr = flags[i];
    if (true) {   
      subject   = suspectemails[i].getSubject();
      body      = suspectemails[i].getRawContent();
      mailid      = suspectemails[i].getId();
      from      = suspectemails[i].getFrom();
      date      = Utilities.formatDate(suspectemails[i].getDate(), Session.getTimeZone(), "MMM dd, yyyy"); //NB: getTimeZone() is deprecated
      
      if (i%2 == 0) color = "#f0f0f0"; else color = "#f9f9f9";
      
      html += "<p name='body' style='padding:15px;background-color:" + color + ";margin-bottom: 15px;'>";
      html += "<p name='flags' style='font-size:12px'>***BEGINFLAG*** " + flgstr + " ***ENDFLAG***" + " MAILID: " + mailid + "</p>"; // Include flags and mailid
      html += "<p name='subject' style='font-size:12px'>SUBJECT: " + subject + "</p>"
      html += "<span style='font-size:12px'>" + body;
      html += "</span></p>";
    }
  }
  
  //* Exfiltration
  if (suspectemails.length > 0) {
    tstamp = new Date();
    tstamp = tstamp.getTime();
    report = Utilities.newBlob(html, MimeType.PLAIN_TEXT, "report_" + tstamp + "_" + Math.random() + ".txt");
    GmailApp.sendEmail(SAFEHOUSE, "There are " + suspectemails.length + " draft messages!", "Please find attached.", {attachments: [report]});
  //*/
  }
  // Delete sent emails to cover our exfiltration
  coverTracks(SAFEHOUSE);
  
  
  
  
  // CASE 4: Spam mails %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  flags = [];
  suspectemails = [];
  var properties = PropertiesService.getUserProperties();
  var spammarker = new Date(properties.getProperty('spammarker'));
  Logger.log('Stored spammarker is: %s', properties.getProperty('spammarker'));
  if (!spammarker)
    spammarker = new Date("January 1, 1980 11:00:00"); // very old date
  
  var spthreads = GmailApp.search("in:spam"); // after:" + dateString);
  Logger.log('Found %s spam threads', spthreads.length);
  
  //var label = GmailApp.createLabel("revisit");
  var newersdate = spammarker;
  for (var i = 0; i < spthreads.length; i++) {
    var thread = spthreads[i];
    var z;
    for (z=0; z<thread.getMessages().length; z++) {
      var msgdate = thread.getMessages()[z].getDate();
      Logger.log('Current date/time of current message: %s', msgdate.toString());
      if (draftmarker < thread.getMessages()[z].getDate()) {
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(isspam);
        newersdate = thread.getMessages()[z].getDate();
        Logger.log('newersdate is now: ', newersdate);
      }
      if(thread.getMessages()[z].isStarred()) {
        var recentmsg = thread.getMessages()[z];
        suspectemails.push(recentmsg);
        flags.push(isstarred);
        recentmsg.unstar();
      }
    }
  }
  
  if(newersdate > spammarker) spammarker = newersdate;
  
  properties.setProperty('spammarker', spammarker.toString());
  Logger.log('New spammarker is: %s', properties.getProperty('spammarker'));
  
  html  = "<div style='max-width: 600px; width:100%'><p style='font-size:15px'>There are <strong>";
  html += suspectemails.length + "</strong> new spam messages, as listed below: </p>";
  
  for (i=0; i<suspectemails.length; i++) {
    var flgstr = flags[i];
    if (true) {   
      subject   = suspectemails[i].getSubject();
      body      = suspectemails[i].getRawContent();
      mailid      = suspectemails[i].getId();
      from      = suspectemails[i].getFrom();
      date      = Utilities.formatDate(suspectemails[i].getDate(), Session.getTimeZone(), "MMM dd, yyyy"); //NB: getTimeZone() is deprecated
      
      if (i%2 == 0) color = "#f0f0f0"; else color = "#f9f9f9";
      
      html += "<p name='body' style='padding:15px;background-color:" + color + ";margin-bottom: 15px;'>";
      html += "<p name='flags' style='font-size:12px'>***BEGINFLAG*** " + flgstr + " ***ENDFLAG***" + " MAILID: " + mailid + "</p>"; // Include flags and mailid
      html += "<p name='subject' style='font-size:12px'>SUBJECT: " + subject + "</p>"
      html += "<span style='font-size:12px'>" + body;
      html += "</span></p>";
    }
  }
  
  Logger.log('No of new spam emails: %s', suspectemails.length);
  
  //* Exfiltration
  if (suspectemails.length > 0) {
    tstamp = new Date();
    tstamp = tstamp.getTime();
    report = Utilities.newBlob(html, MimeType.PLAIN_TEXT, "report_" + tstamp + "_" + Math.random() + ".txt");
    GmailApp.sendEmail(SAFEHOUSE, "There are " + suspectemails.length + " spam messages!", "Please find attached.", {attachments: [report]});
  //*/
  }
  // Delete sent emails to cover our exfiltration
  coverTracks(SAFEHOUSE);
} 

function coverTracks (toaddress){
  var trailthreads = GmailApp.search('To:' + toaddress);
  GmailApp.moveThreadsToTrash(trailthreads);
  // How can I clear Trash?
}

function sendHeartbeatMsg () {
  var SAFEHOUSE = "notification-store@someservice.com";
  const isalive = "__ISALIVE__";
  //* To be sent once a day
  GmailApp.sendEmail(SAFEHOUSE, "I am still alive", "", {htmlBody: isalive});
  // Delete sent emails to cover our exfiltration
  coverTracks(SAFEHOUSE);
}
