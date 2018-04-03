import logging
import os

logger = logging.getLogger(__name__)

import dateutil.parser


class PLTFileReader(object):
    USER_ID_INDEX = -3

    def __init__(self, path):
        self.path = path

        # extract useful information from file
        self.user = int(path.split(os.sep)[self.USER_ID_INDEX])

        # get the first timestamp of the first record in the file
        file = self.open()
        first_line = next(file)
        file.close()

        self.start_time = PLTPoint(line=first_line).timestamp

    def open(self):
        '''Open .plt file and skip the first few lines.'''
        gps_log = open(self.path)
        for _ in range(6):
            next(gps_log)
        return gps_log

    def __iter__(self):
        log = self.open()
        for line in log:
            yield PLTPoint(line=line)
        log.close()

    def __len__(self):
        log = self.open()
        return len(list(log))


class PLTPoint(object):
    LATITUDE_INDEX = 0
    LONGITUDE_INDEX = 1
    DATE_INDEX = -2
    TIME_INDEX = -1

    def __init__(self, line):
        # Split the lines into seperate fields
        # '39.890275,116.453691,0,157,39925.4486111111,2009-04-22,10:46:00'
        #       mapped to
        # ['39.890275', '116.453691', '0', '157', '39925.4486111111',
        #  '2009-04-22', '10:46:00']
        self.line = line.rstrip().split(',')

    @property
    def latitude(self):
        # Extract only the lat, long, date, and time fields, merging the
        #   date and time fields, and convert to the appropriate data types
        # ['39.890275', '116.453691', '0', '157', '39925.4486111111',
        #  '2009-04-22', '10:46:00']
        #       mapped to
        #     * latitude: 39.890275
        #     * longitude: 116.453691
        #     * timestamp: datetime.datetime(2009, 4, 22, 10, 46)
        return float(self.line[self.LATITUDE_INDEX])

    @property
    def longitude(self):
        return float(self.line[self.LONGITUDE_INDEX])

    @property
    def timestamp(self):
        return dateutil.parser.parse(' '.join([
            self.line[self.DATE_INDEX],
            self.line[self.TIME_INDEX]
        ]))

    def __str__(self):
        return '({0.latitude}, {0.longitude}) @{0.timestamp}'.format(self)


class GPSTrajectory(object):
    def __init__(self, time_interval_threshold, initial_point=None):
        self.threshold = time_interval_threshold

        self.points = []
        if initial_point is not None:
            self.points.append(initial_point)

    def add_point(self, point):
        if not self.points:
            self.points.append(point)
            return True

        else:
            time_difference = point.timestamp - self.latest_time
            # logger.debug('Time difference between points: {}'.format(time_difference))
            if time_difference >= self.threshold:
                return False

            else:
                self.points.append(point)
                return True

    @property
    def latest_time(self):
        return self.points[-1].timestamp

    def __str__(self):
        start = self.points[0].timestamp
        end = self.latest_time
        return '{point_count: >4} points, {start} to {end} ' \
               '({time_difference})'.format(
            point_count=len(self.points),
            start=start,
            end=end,
            time_difference=end-start,
        )
