Changelog
=========

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
