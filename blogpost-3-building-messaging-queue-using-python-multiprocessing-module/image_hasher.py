import os
import sys
import time
from collections import defaultdict
from Queue import Queue, Empty
from threading import Thread, Event, Condition, current_thread

from file_finder import ImageFinder
from photohash.photohash import average_hash

class ImageHasher(object):

    def __init__(self, src_path, outbox, workers_count=5):
        
        #image directory path
        self.src_path = src_path

        #inbox: queue to store unprocessed image 
        #from which threads will read the unprocessed image path
        self.inbox = Queue()

        #queue where threads will write the calculated hash and
        #the path of image as a tuple
        self.outbox = outbox

        #failed images will be logged here
        self.error = Queue()

        #event to watch for shutdown
        self.shutdown = Event()

        #event to indicate workers that 
        #we are done sending data
        self.done = Event()

        #condition to signal when queue is not empty
        self.empty = Condition()

        self.workers = []
        self.workers_count = workers_count

    def _worker(self):
        '''
        This is the worker which will get the image from 'inbox',
        calculate the hash and puts the result in 'outbox'
        '''

        while not self.shutdown.isSet():
            
            try:
                image_path = self.inbox.get_nowait()
            except Empty:
                print 'no data found. isset: ' , self.done.isSet()
                if not self.done.isSet():
                    with self.empty:
                        self.empty.wait()
                        continue
                else:
                    break

            if not os.path.exists(image_path):
                self.error((image_path, 'Image Does not Exist'))
                
            try:
                print '[%s] Processing %s' % (current_thread().ident, image_path)
                image_hash = average_hash(image_path)
                self.outbox.put((image_hash, image_path))
            except IOError as err:
                print 'ERROR: Got %s for image : %s' % (image_path, err)
        print 'Worker %s has done processing.' % current_thread().ident

    def _start_workers(self):
        '''method to start all the worker threads'''
        for _ in range(self.workers_count):
            worker = Thread(target=self._worker)
            worker.start()
            self.workers.append(worker)

    def start(self):
        
        #lets start workers
        self._start_workers()
        print 'Workers are started. Waiting for work...'

        #find images to put in inbox, workers are waiting
        images_path = ImageFinder.ifind(self.src_path)
        for image_path in images_path:
            print 'Found image: %s' % image_path
            with self.empty:
                #acquire the condition lock, put image path in inbox queue
                #and notify the worker thread who is waiting for an item to be put in the inbox queue
                self.inbox.put_nowait(image_path)
                self.empty.notify()

        #lets tell every worker we are done sending data
        #and exit once they are get Empty exception
        self.done.set()

        print 'All images has been sent to worker. Waiting to finish'
        #all we have to do now is wait for
        #workers to finish processing
        for worker in self.workers:
            worker.join()
            print 'Worker %s has done processing' % (worker.ident)

        #now that we have all the images processed
        #lets see how many duplicates are there
        dupe_images = defaultdict(list)
        while True:
            try:
                (image_hash, image_path) = self.outbox.get_nowait()
                dupe_images[image_hash].append(image_path)
            except Empty:
                break

        for _hash, _paths in dupe_images.iteritems():
            print 'Hash: %s DupeCount: %s Paths: %s' % (_hash, len(_paths), ','.join(_paths))
