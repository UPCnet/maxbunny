Changelog
=========

5.8 (2022-03-18)
----------------

* Acortar mensaje para solucionar que Firebase no envie notificación push si el MessageTooBig [Pilar Marinas]
* Test push modificados porque ya no funciona el Google Cloud Messaging (GCM) van todos por Firebase Cloud Messaging (FCM) [Pilar Marinas]
* Comentado que no envie notificaciones push APP uTalk antigua certificados ios y android caducados [pilar.marinas]

5.7 (2019-05-20)
----------------

* Sonido en la notificacion push firebase [Pilar Marinas]

5.6 (2018-02-15)
----------------

* Merge remote-tracking branch 'origin/develop' [Pilar Marinas]
* Resolve error test [Pilar Marinas]
* Display name of group in Push notification [Pilar Marinas]
* Text Push Add image in activity [Pilar Marinas]
* Text Push Add image [Pilar Marinas]

5.5 (2018-01-18)
----------------

* Merge remote-tracking branch 'origin/develop' [Pilar Marinas]
* Cambios para que funcione la nueva APP Utalk con notificaciones push Firebase [Pilar Marinas]

5.4 (2016-11-16)
----------------

* Solucionar conflicte [Pilar Marinas]
5.3 (2016-07-25)
----------------

* Delete failed tokens [Carles Bruguera]
* Fix subscription mocker [Carles Bruguera]
* Fix token platform case check [Carles Bruguera]

5.2 (2015-10-29)
----------------

* Safe check for token status [Carles Bruguera]

5.1 (2015-05-28)
----------------

* Fix overlapped releases

5.0 (2015-05-19)
----------------

* Move get domain client to base consumer [Carles Bruguera]
* Test consumer exceptions [Carles Bruguera]
* Fine tune logs & move multiprocess spawn to runner [Carles Bruguera]
* PEP8, remove unused code and general Cleanup [Carles Bruguera]
* Use thread on mocket rabbit tests [Carles Bruguera]
* Test conversation & activity push [Carles Bruguera]
* Remove mocking from conversation tests, running rabbitmq is mandatory [Carles Bruguera]
* Document mockers [Carles Bruguera]
* Cleanup [Carles Bruguera]
* Test android [Carles Bruguera]
* test pushdebug [Carles Bruguera]
* Refactor handling of objects in separate methods [Carles Bruguera]
* Refactor android push [Carles Bruguera]
* Handle ios and android exceptions on consumer loop exception handling [Carles Bruguera]
* Move ios specific parts inside send ios method [Carles Bruguera]
* Push tests [Carles Bruguera]
* Refactor handling of error and successes [Carles Bruguera]
* Base for push tests [Carles Bruguera]
* Increment waiting time for mails [Carles Bruguera]
* Test non-json message, fix error logs location [Carles Bruguera]
* Fix Requeue exception handling [Carles Bruguera]
* Test Requeing without uuid [Carles Bruguera]
* SMTP Mocker, fix runner ini param [Carles Bruguera]
* Start consume loop as a thread [Carles Bruguera]
* Output reason of forced close [Carles Bruguera]
* Fix BunnyConsumer test spawning multiprocess [Carles Bruguera]
* Make MockLogger log to file, to fix problem in multiprocessing [Carles Bruguera]
* Test error from max [Carles Bruguera]
* Remove unused image processing code [Carles Bruguera]
* Check push queue on all tests [Carles Bruguera]
* Set httpretty so won't block haigha requests [Carles Bruguera]
* Test push queue reception [Carles Bruguera]
* Add default instance to instances2.ini [Carles Bruguera]
* Use real clients wrapper [Carles Bruguera]
* Instances defined in file, with a mock runner param [Carles Bruguera]
* Use parsed json body [Carles Bruguera]
* Make clients wrapper reload itself when needed [Carles Bruguera]
* Fix test descriptions [Carles Bruguera]
* Organize mockers [Carles Bruguera]
* Prepare test_conversations [Carles Bruguera]
* Rename tweety mocks [Carles Bruguera]
* Avoid iterating users twice [Carles Bruguera]
* Move remaining literal into var [Carles Bruguera]
* Test debug hashtag [Carles Bruguera]
* Cache queries, only once for each call to process [Carles Bruguera]
* Test all remaining scenarios [Carles Bruguera]
* Remove unnecessary nesting [Carles Bruguera]
* Alert on hashtag mesagee not posting to multiple max servers [Carles Bruguera]
* Method and variable rename for clarity [Carles Bruguera]
* Add tests scenarios descriptions [Carles Bruguera]
* Create mockers for new maxbunny [Carles Bruguera]
* Adapt tweety tests [Carles Bruguera]
* Single-process debug mode [Carles Bruguera]
* Change to docopt to parse options [Carles Bruguera]
* Be more explicit on client loading failure [Carles Bruguera]
* Don't Cancel at method end [Carles Bruguera]

4.0.16 (2014-12-04)
-------------------

* Make notify conditional on BunnyMessageCancel [Carles Bruguera]
* Choose what exceptions send notifications [Carles Bruguera]
* Don't send mail if there are no recipients [Carles Bruguera]

4.0.15 (2014-12-04)
-------------------

* Use WatchedFileHandler to be aware of logrotate [Carles Bruguera]
* Default must be a list [Carles Bruguera]

4.0.14 (2014-12-01)
-------------------

* Recover SSL method patch [Carles Bruguera]

4.0.13 (2014-12-01)
-------------------

* Handle TERM signal to stop all workers [Carles Bruguera]

4.0.12 (2014-11-27)
-------------------

* Depend on gevent [Carles Bruguera]

4.0.11 (2014-11-25)
-------------------

* Don't crash if user data missing [Carles Bruguera]

4.0.10 (2014-11-25)
-------------------

* Don't crash if maxserver not available [Carles Bruguera]
* Unify instances file format with bigmax [Carles Bruguera]
* Improve logging of reqeues and drops [Carles Bruguera]
* Parametrize mail settings [Carles Bruguera]
* Send and log drops [Carles Bruguera]
* Refactor maxbunny using multiprocessing approach [Carles Bruguera]
* Do not try to send push if keys not configured [Carles Bruguera]
* Fix default domain getter [Carles Bruguera]

4.0.9 (2014-10-27)
------------------

* Patch to solve SSLv3 deprecation from apple [Carles Bruguera]
* Move patches to patches.py [Carles Bruguera]
* Fix "da mediolanum bug" [Carles Bruguera]
* Pin apns-client [Carles Bruguera]
* Set custom client properties [Carles Bruguera]
* WEIRDEST BUG EVER, lstrip, strips *char-by-char* [Carles Bruguera]

4.0.8 (2014-07-29)
------------------

* Do not send push to sender unless #pushdebug found [Carles Bruguera]
* Store id in ack_message [Carles Bruguera]
* Include routing_key as message destination [Carles Bruguera]

4.0.7 (2014-07-16)
------------------

* Fine tune workarounds [Carles Bruguera]
* Added workaround to send image and new conversations push [Carles Bruguera]
* Don't assume there will be always a text inside data [Carles Bruguera]
* Don't ignore conversation object in messages [Carles Bruguera]
* Fix unicodeEncode bug [Carles Bruguera]
* Require extra wsgi feature from maxclient [Carles Bruguera]

4.0.6 (2014-07-08)
------------------

* Don't send notification to same device token twice [Carles Bruguera]

4.0.5 (2014-07-08)
------------------

* Send notification ack from users publish exchange [Carles Bruguera]
* Remove domain woraround [Carles Bruguera]
* Better processing of messages without domain [Carles Bruguera]
* Send notification to user publish exchange, to use binding filters [Carles Bruguera]
* Cancel message if invalid conversation [Carles Bruguera]

4.0.4 (2014-06-11)
------------------

* Be aware of messages from notifications [Carles Bruguera]

4.0.3 (2014-06-10)
------------------

* Incorporate production patch [Carles Bruguera]
* Save requeue exceptions on a disk log [Carles Bruguera]
* requeue conversation messages to push [Carles Bruguera]
* Fix temporary fix ¬_¬ ... [Carles Bruguera]

4.0.2 (2014-05-12)
------------------

* Apply workaround to push consumer [Carles Bruguera]
* Fix pick client [Carles Bruguera]
* provisional workaround to search for correct domain [Carles Bruguera]
* Better logging and error handling [Carles Bruguera]

4.0.1 (2014-05-08)
------------------

* Log messages via exception [Carles Bruguera]
* Propagate filename [Carles Bruguera]
* Non-mandatory text field for image and file [Carles Bruguera]
* Adapt to new file upload specification [Carles Bruguera]
* Fix nack call [Carles Bruguera]
* tune-up converastions posts with images [Carles Bruguera]
* post messages with images and files [Carles Bruguera]
* Fix SSL patch for recv() [Carles Bruguera]
* Send extra data on ios payload [Carles Bruguera]
* React to not found exceptions [Carles Bruguera]
* Distinguish between activity or message in push delivery [Carles Bruguera]

4.0.0 (2014-04-15)
------------------

* New version of maxbunny using gevent & rabbitpy WIP [Carles Bruguera]
* Reread config file if asked for unknown client [Carles Bruguera]

1.4.1 (2013-11-11)
------------------

* Catched twitter duplications bug, #atlast [Carles Bruguera]

1.4 (2013-11-07)
----------------

* Log duplicated tweets apart [Carles Bruguera]
* Send message as string on iOS [Carles Bruguera]

1.3 (2013-10-29)
----------------

* Fix wrong key name [Carles Bruguera]
* Include message properties in notifications [Carles Bruguera]

1.2 (2013-10-17)
----------------

* no limit in max response lists [Carles Bruguera]

1.1 (2013-10-03)
----------------

 * Don't crash when receiving a debug hashtag [Carles Bruguera]
 * Adapt maxbunny to new ini files layout [Carles Bruguera]
 * Fix restricted user bug [Carles Bruguera]
 * Configure logs [Carles Bruguera]
 * New version [Victor Fernandez de Alba]
 * Enable push android [Victor Fernandez de Alba]
 * fix [Victor Fernandez de Alba]
 * Added Android push [Victor Fernandez de Alba]
 * WIP Android push [Victor Fernandez de Alba]
 * Merge branch 'develop' of github.com:UPCnet/maxbunny into develop [Oriol Bosch]
 * Better guards for error handling [Oriol Bosch]
 * Wrong variable name [Carles Bruguera]
 * Change rabbitmq connection parameters method Cleanup unused config options [Carles Bruguera]
 * Make use of rabbitmq buildout ports [Carles Bruguera]

----------------

-  Initial version
