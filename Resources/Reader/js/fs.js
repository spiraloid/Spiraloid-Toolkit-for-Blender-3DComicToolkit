"use strict";
var __extends = (this && this.__extends) || function (d, b) {
    for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
    function __() { this.constructor = d; }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var libjs = require('../libjs/libjs');
var libaio = require('../libaio/libaio');
var pathModule = require('path');
var events_1 = require('events');
var buffer_1 = require('buffer');
//     interface ObjectConstructor {
//         assign(...args: any[]): any;
//     }
//
//      extend = Object.assign;
function extend(a, b) {
    for (var i in b)
        a[i] = b[i];
    return a;
}
var fs = exports;
function noop() { }
function throwError(errno, func, path, path2) {
    if (func === void 0) { func = ''; }
    if (path === void 0) { path = ''; }
    if (path2 === void 0) { path2 = ''; }
    // console.log(-errno, libjs.ERROR.EBADF);
    switch (-errno) {
        case 2 /* ENOENT */: throw Error("ENOENT: no such file or directory, " + func + " '" + path + "'");
        case 9 /* EBADF */: throw Error("EBADF: bad file descriptor, " + func);
        case 22 /* EINVAL */: throw Error("EINVAL: invalid argument, " + func);
        case 1 /* EPERM */: throw Error("EPERM: operation not permitted, " + func + " '" + path + "' -> '" + path2 + "'");
        case 71 /* EPROTO */: throw Error("EPROTO: protocol error, " + func + " '" + path + "' -> '" + path2 + "'");
        case 17 /* EEXIST */: throw Error("EEXIST: file already exists, " + func + " '" + path + "' -> '" + path2 + "'");
        default: throw Error("Error occurred in " + func + ": errno = " + errno);
    }
}
function validPathOrThrow(path) {
    if (path instanceof buffer_1.Buffer)
        path = path.toString();
    if (typeof path !== 'string')
        throw TypeError('path must be a string');
    return path;
}
function validateFd(fd) {
    if (typeof fd !== 'number')
        throw TypeError('fd must be a file descriptor');
}
// List of file `flags` as defined by node.
(function (flags) {
    // Open file for reading. An exception occurs if the file does not exist.
    flags[flags["r"] = 0] = "r";
    // Open file for reading and writing. An exception occurs if the file does not exist.
    flags[flags['r+'] = 2] = 'r+';
    // Open file for reading in synchronous mode. Instructs the operating system to bypass the local file system cache.
    flags[flags["rs"] = 1069056] = "rs";
    // Open file for reading and writing, telling the OS to open it synchronously. See notes for 'rs' about using this with caution.
    flags[flags['rs+'] = 1069058] = 'rs+';
    // Open file for writing. The file is created (if it does not exist) or truncated (if it exists).
    flags[flags["w"] = 577] = "w";
    // Like 'w' but fails if path exists.
    flags[flags["wx"] = 705] = "wx";
    // Open file for reading and writing. The file is created (if it does not exist) or truncated (if it exists).
    flags[flags['w+'] = 578] = 'w+';
    // Like 'w+' but fails if path exists.
    flags[flags['wx+'] = 706] = 'wx+';
    // Open file for appending. The file is created if it does not exist.
    flags[flags["a"] = 1089] = "a";
    // Like 'a' but fails if path exists.
    flags[flags["ax"] = 1217] = "ax";
    // Open file for reading and appending. The file is created if it does not exist.
    flags[flags['a+'] = 1090] = 'a+';
    // Like 'a+' but fails if path exists.
    flags[flags['ax+'] = 1218] = 'ax+';
})(exports.flags || (exports.flags = {}));
var flags = exports.flags;
var MODE_DEFAULT = 438;
exports.F_OK = 0 /* F_OK */;
exports.R_OK = 4 /* R_OK */;
exports.W_OK = 2 /* W_OK */;
exports.X_OK = 1 /* X_OK */;
function accessSync(path, mode) {
    if (mode === void 0) { mode = exports.F_OK; }
    var vpath = validPathOrThrow(path);
    var res = libjs.access(vpath, mode);
    if (res < 0)
        throwError(res, 'access', vpath);
}
exports.accessSync = accessSync;
var appendFileDefaults = {
    encoding: 'utf8',
    mode: MODE_DEFAULT,
    flag: 'a'
};
function appendFile(file, data, options, callback) { }
exports.appendFile = appendFile;
function appendFileSync(file, data, options) {
    if (options === void 0) { options = {}; }
    options = extend(options, appendFileDefaults);
}
exports.appendFileSync = appendFileSync;
function chmod(path, mode, callback) { }
exports.chmod = chmod;
function chmodSync(path, mode) {
    var vpath = validPathOrThrow(path);
    if (typeof mode !== 'number')
        throw TypeError('mode must be an integer');
    var result = libjs.chmod(vpath, mode);
    if (result < 0)
        throwError(result, 'chmod', vpath);
}
exports.chmodSync = chmodSync;
function fchmod(fd, mode, callback) { }
exports.fchmod = fchmod;
function fchmodSync(fd, mode) {
    validateFd(fd);
    if (typeof mode !== 'number')
        throw TypeError('mode must be an integer');
    var result = libjs.fchmod(fd, mode);
    if (result < 0)
        throwError(result, 'chmod');
}
exports.fchmodSync = fchmodSync;
// Mac OS only:
//     export function lchmodSync(path: string|Buffer, mode: number) {}
function chown(path, uid, gid, callback) { }
exports.chown = chown;
function chownSync(path, uid, gid) {
    var vpath = validPathOrThrow(path);
    if (typeof uid !== 'number')
        throw TypeError('uid must be an unsigned int');
    if (typeof gid !== 'number')
        throw TypeError('gid must be an unsigned int');
    var result = libjs.chown(vpath, uid, gid);
    if (result < 0)
        throwError(result, 'chown', vpath);
}
exports.chownSync = chownSync;
function fchown(fd, uid, gid, callback) { }
exports.fchown = fchown;
function fchownSync(fd, uid, gid) {
    validateFd(fd);
    if (typeof uid !== 'number')
        throw TypeError('uid must be an unsigned int');
    if (typeof gid !== 'number')
        throw TypeError('gid must be an unsigned int');
    var result = libjs.fchown(fd, uid, gid);
    if (result < 0)
        throwError(result, 'fchown');
}
exports.fchownSync = fchownSync;
function lchown(path, uid, gid, callback) { }
exports.lchown = lchown;
function lchownSync(path, uid, gid) {
    var vpath = validPathOrThrow(path);
    if (typeof uid !== 'number')
        throw TypeError('uid must be an unsigned int');
    if (typeof gid !== 'number')
        throw TypeError('gid must be an unsigned int');
    var result = libjs.lchown(vpath, uid, gid);
    if (result < 0)
        throwError(result, 'lchown', vpath);
}
exports.lchownSync = lchownSync;
function closeSync(fd) {
    if (typeof fd !== 'number')
        throw TypeError('fd must be a file descriptor');
    var result = libjs.close(fd);
    if (result < 0)
        throwError(result, 'close');
}
exports.closeSync = closeSync;
// var readStreamOptionsDefaults: IReadStreamOptions = {
//     flags: 'r',
//     encoding: null,
//     fd: null,
//     mode: MODE_DEFAULT,
//     autoClose: true,
// };
// export function createReadStream(path: string|Buffer, options: IReadStreamOptions|string = {}) {
//     options = extend(options, readStreamOptionsDefaults);
// }
function createWriteStream(path, options) { }
exports.createWriteStream = createWriteStream;
function existsSync(path) {
    console.log('Deprecated fs.existsSync(): Use fs.statSync() or fs.accessSync() instead.');
    try {
        accessSync(path);
        return true;
    }
    catch (e) {
        return false;
    }
}
exports.existsSync = existsSync;
function fsyncSync(fd) {
    if (typeof fd !== 'number')
        throw TypeError('fd must be a file descriptor');
    var result = libjs.fsync(fd);
    if (result < 0)
        throwError(result, 'fsync');
}
exports.fsyncSync = fsyncSync;
function fdatasyncSync(fd) {
    if (typeof fd !== 'number')
        throw TypeError('fd must be a file descriptor');
    var result = libjs.fdatasync(fd);
    if (result < 0)
        throwError(result, 'fdatasync');
}
exports.fdatasyncSync = fdatasyncSync;
var Stats = (function () {
    function Stats() {
    }
    Stats.prototype.isFile = function () {
        return (this.mode & 32768 /* IFREG */) == 32768 /* IFREG */;
    };
    Stats.prototype.isDirectory = function () {
        return (this.mode & 16384 /* IFDIR */) == 16384 /* IFDIR */;
    };
    Stats.prototype.isBlockDevice = function () {
        return (this.mode & 24576 /* IFBLK */) == 24576 /* IFBLK */;
    };
    Stats.prototype.isCharacterDevice = function () {
        return (this.mode & 8192 /* IFCHR */) == 8192 /* IFCHR */;
    };
    Stats.prototype.isSymbolicLink = function () {
        return (this.mode & 40960 /* IFLNK */) == 40960 /* IFLNK */;
    };
    Stats.prototype.isFIFO = function () {
        return (this.mode & 4096 /* IFIFO */) == 4096 /* IFIFO */;
    };
    Stats.prototype.isSocket = function () {
        return (this.mode & 49152 /* IFSOCK */) == 49152 /* IFSOCK */;
    };
    return Stats;
}());
exports.Stats = Stats;
function createStatsObject(res) {
    var stats = new Stats;
    stats.dev = res.dev;
    stats.mode = res.mode;
    stats.nlink = res.nlink;
    stats.uid = res.uid;
    stats.gid = res.gid;
    stats.rdev = res.rdev;
    stats.blksize = res.blksize;
    stats.ino = res.ino;
    stats.size = res.size;
    stats.blocks = res.blocks;
    stats.atime = new Date(res.atime * 1000);
    stats.mtime = new Date(res.mtime * 1000);
    stats.ctime = new Date(res.ctime * 1000);
    stats.birthtime = stats.ctime;
    return stats;
}
function statSync(path) {
    var vpath = validPathOrThrow(path);
    try {
        var res = libjs.stat(vpath);
        return createStatsObject(res);
    }
    catch (errno) {
        throwError(errno, 'stat', vpath);
    }
}
exports.statSync = statSync;
function fstatSync(fd) {
    validateFd(fd);
    try {
        var res = libjs.fstat(fd);
        return createStatsObject(res);
    }
    catch (errno) {
        throwError(errno, 'fstat');
    }
}
exports.fstatSync = fstatSync;
function lstatSync(path) {
    var vpath = validPathOrThrow(path);
    try {
        var res = libjs.lstat(vpath);
        return createStatsObject(res);
    }
    catch (errno) {
        throwError(errno, 'lstat', vpath);
    }
}
exports.lstatSync = lstatSync;
function truncateSync(path, len) {
    var vpath = validPathOrThrow(path);
    if (typeof len !== 'number')
        throw TypeError('len must be an integer');
    var res = libjs.truncate(vpath, len);
    if (res < 0)
        throwError(res, 'truncate', vpath);
}
exports.truncateSync = truncateSync;
function ftruncateSync(fd, len) {
    validateFd(fd);
    if (typeof len !== 'number')
        throw TypeError('len must be an integer');
    var res = libjs.ftruncate(fd, len);
    if (res < 0)
        throwError(res, 'ftruncate');
}
exports.ftruncateSync = ftruncateSync;
//     TODO: Make this work with `utimes` instead of `utime`, also figure out a way
//     TODO: how to set time using file descriptor, possibly use `utimensat` system call.
function utimesSync(path, atime, mtime) {
    path = validPathOrThrow(path);
    if (typeof atime === 'string')
        atime = parseInt(atime);
    if (typeof mtime === 'string')
        mtime = parseInt(mtime);
    if (typeof atime !== 'number')
        throw TypeError('atime must be an integer');
    if (typeof mtime !== 'number')
        throw TypeError('mtime must be an integer');
    var vatime = atime;
    var vmtime = mtime;
    // if(!Number.isFinite(atime)) atime = Date.now();
    // if(!Number.isFinite(mtime)) mtime = Date.now();
    if (!isFinite(vatime))
        vatime = Date.now();
    if (!isFinite(vmtime))
        vmtime = Date.now();
    // `libjs.utime` works with 1 sec precision.
    vatime = Math.round(vatime / 1000);
    vmtime = Math.round(vmtime / 1000);
    var times = {
        actime: [libjs.UInt64.lo(vatime), libjs.UInt64.hi(vatime)],
        modtime: [libjs.UInt64.lo(vmtime), libjs.UInt64.hi(vmtime)]
    };
    var res = libjs.utime(path, times);
    console.log(res);
    if (res < 0)
        throwError(res, 'utimes', path);
}
exports.utimesSync = utimesSync;
// export function futimesSync(fd: number, atime: number|string, mtime: number|string) {}
function linkSync(srcpath, dstpath) {
    var vsrcpath = validPathOrThrow(srcpath);
    var vdstpath = validPathOrThrow(dstpath);
    var res = libjs.link(vsrcpath, vdstpath);
    if (res < 0)
        throwError(res, 'link', vsrcpath, vdstpath);
}
exports.linkSync = linkSync;
function mkdirSync(path, mode) {
    if (mode === void 0) { mode = MODE_DEFAULT; }
    var vpath = validPathOrThrow(path);
    if (typeof mode !== 'number')
        throw TypeError('mode must be an integer');
    var res = libjs.mkdir(vpath, mode);
    if (res < 0)
        throwError(res, 'mkdir', vpath);
}
exports.mkdirSync = mkdirSync;
function randomString6() {
    return (+new Date).toString(36).slice(-6);
}
function mkdtempSync(prefix, options) {
    if (options === void 0) { options = {}; }
    if (!prefix || typeof prefix !== 'string')
        throw new TypeError('filename prefix is required');
    var retries = 10;
    var fullname;
    var found_tmp_name = false;
    for (var i = 0; i < retries; i++) {
        fullname = prefix + randomString6();
        try {
            accessSync(fullname);
        }
        catch (e) {
            found_tmp_name = true;
            break;
        }
    }
    if (found_tmp_name) {
        mkdirSync(fullname);
        return fullname;
    }
    else {
        throw Error("Could not find a new name, mkdtemp");
    }
}
exports.mkdtempSync = mkdtempSync;
function flagsToFlagsValue(f) {
    if (typeof f === 'number')
        return flags;
    if (typeof f !== 'string')
        throw TypeError("flags must be string or number");
    var flagsval = flags[f];
    if (typeof flagsval !== 'number')
        throw TypeError("Invalid flags string value '" + f + "'");
    return flagsval;
}
function openSync(path, flags, mode) {
    if (mode === void 0) { mode = MODE_DEFAULT; }
    var vpath = validPathOrThrow(path);
    var flagsval = flagsToFlagsValue(flags);
    if (typeof mode !== 'number')
        throw TypeError('mode must be an integer');
    var res = libjs.open(vpath, flagsval, mode);
    if (res < 0)
        throwError(res, 'open', vpath);
    return res;
}
exports.openSync = openSync;
function readSync(fd, buffer, offset, length, position) {
    validateFd(fd);
    if (!(buffer instanceof buffer_1.Buffer))
        throw TypeError('buffer must be an instance of Buffer');
    if (typeof offset !== 'number')
        throw TypeError('offset must be an integer');
    if (typeof length !== 'number')
        throw TypeError('length must be an integer');
    if (position !== null) {
        if (typeof position !== 'number')
            throw TypeError('position must be an integer');
        var seekres = libjs.lseek(fd, position, 0 /* SET */);
        if (seekres < 0)
            throwError(seekres, 'read');
    }
    var buf = buffer.slice(offset, offset + length);
    var res = libjs.read(fd, buf);
    if (res < 0)
        throwError(res, 'read');
    return res;
}
exports.readSync = readSync;
var optionsDefaults = {
    encoding: 'utf8'
};
function readdirSync(path, options) {
    if (options === void 0) { options = {}; }
    var vpath = validPathOrThrow(path);
    options = extend(options, optionsDefaults);
    return libjs.readdirList(vpath, options.encoding);
}
exports.readdirSync = readdirSync;
var readFileOptionsDefaults = {
    flag: 'r'
};
function readFileSync(file, options) {
    if (options === void 0) { options = {}; }
    var opts;
    if (typeof options === 'string')
        opts = extend({ encoding: options }, readFileOptionsDefaults);
    else if (typeof options !== 'object')
        throw TypeError('Invalid options');
    else
        opts = extend(options, readFileOptionsDefaults);
    if (opts.encoding && (typeof opts.encoding != 'string'))
        throw TypeError('Invalid encoding');
    var fd;
    if (typeof file === 'number')
        fd = file;
    else {
        var vfile = validPathOrThrow(file);
        var flag = flags[opts.flag];
        fd = libjs.open(vfile, flag, MODE_DEFAULT);
        if (fd < 0)
            throwError(fd, 'readFile', vfile);
    }
    var CHUNK = 4096;
    var list = [];
    do {
        var buf = new buffer_1.Buffer(CHUNK);
        var res = libjs.read(fd, buf);
        if (res < CHUNK)
            buf = buf.slice(0, res);
        list.push(buf);
        if (res < 0)
            throwError(res, 'readFile');
    } while (res > 0);
    libjs.close(fd);
    var buffer = buffer_1.Buffer.concat(list);
    if (opts.encoding)
        return buffer.toString(opts.encoding);
    else
        return buffer;
}
exports.readFileSync = readFileSync;
function readlinkSync(path, options) {
    if (options === void 0) { options = null; }
    path = validPathOrThrow(path);
    var buf = new buffer_1.Buffer(64);
    var res = libjs.readlink(path, buf);
    if (res < 0)
        throwError(res, 'readlink', path);
    var encoding = 'buffer';
    if (options) {
        if (typeof options === 'string')
            encoding = options;
        else if (typeof options === 'object') {
            if (typeof options.encoding != 'string')
                throw TypeError('Encoding must be string.');
            else
                encoding = options.encoding;
        }
        else
            throw TypeError('Invalid options.');
    }
    buf = buf.slice(0, res);
    return encoding == 'buffer' ? buf : buf.toString(encoding);
}
exports.readlinkSync = readlinkSync;
function renameSync(oldPath, newPath) {
    var voldPath = validPathOrThrow(oldPath);
    var vnewPath = validPathOrThrow(newPath);
    var res = libjs.rename(voldPath, vnewPath);
    if (res < 0)
        throwError(res, 'rename', voldPath, vnewPath);
}
exports.renameSync = renameSync;
function rmdirSync(path) {
    var vpath = validPathOrThrow(path);
    var res = libjs.rmdir(vpath);
    if (res < 0)
        throwError(res, 'rmdir', vpath);
}
exports.rmdirSync = rmdirSync;
function symlinkSync(target, path /*, type?: string*/) {
    var vtarget = validPathOrThrow(target);
    var vpath = validPathOrThrow(path);
    // > The type argument [..] is only available on Windows (ignored on other platforms)
    /* type = typeof type === 'string' ? type : null; */
    var res = libjs.symlink(vtarget, vpath);
    if (res < 0)
        throwError(res, 'symlink', vtarget, vpath);
}
exports.symlinkSync = symlinkSync;
function unlinkSync(path) {
    var vpath = validPathOrThrow(path);
    var res = libjs.unlink(vpath);
    if (res < 0)
        throwError(res, 'unlink', vpath);
}
exports.unlinkSync = unlinkSync;
var FSWatcher = (function (_super) {
    __extends(FSWatcher, _super);
    function FSWatcher() {
        _super.apply(this, arguments);
        this.inotify = new libaio.Inotify;
    }
    FSWatcher.prototype.start = function (filename, persistent, recursive, encoding) {
        var _this = this;
        this.inotify.encoding = encoding;
        this.inotify.onerror = noop;
        this.inotify.onevent = function (event) {
            var is_rename = (event.mask & 192 /* MOVE */) || (event.mask & 256 /* CREATE */);
            if (is_rename) {
                _this.emit('change', 'rename', event.name);
            }
            else {
                _this.emit('change', 'change', event.name);
            }
        };
        this.inotify.start();
        this.inotify.addPath(filename);
    };
    FSWatcher.prototype.close = function () {
        this.inotify.stop();
        this.inotify = null;
    };
    return FSWatcher;
}(events_1.EventEmitter));
exports.FSWatcher = FSWatcher;
var watchOptionsDefaults = {
    encoding: 'utf8',
    persistent: true,
    recursive: false
};
// Phew, lucky us:
//
// > The recursive option is only supported on OS X and Windows.
function watch(filename, options, listener) {
    var vfilename = validPathOrThrow(filename);
    vfilename = pathModule.resolve(vfilename);
    var otps;
    if (options) {
        if (typeof options === 'function') {
            listener = options;
            otps = watchOptionsDefaults;
        }
        else if (typeof options === 'string') {
            otps = extend({ encoding: options }, watchOptionsDefaults);
        }
        else if (typeof options === 'object') {
            otps = extend(options, watchOptionsDefaults);
        }
        else
            throw TypeError('"options" must be a string or an object');
    }
    else
        otps = watchOptionsDefaults;
    var watcher = new FSWatcher;
    watcher.start(vfilename, otps.persistent, otps.recursive, otps.encoding);
    if (listener) {
        if (typeof listener !== 'function')
            throw TypeError('"listener" must be a callback');
        watcher.on('change', listener);
    }
    return watcher;
}
exports.watch = watch;
var StatWatcher = (function (_super) {
    __extends(StatWatcher, _super);
    function StatWatcher() {
        _super.apply(this, arguments);
        this.last = null;
    }
    StatWatcher.prototype.loop = function () {
        var _this = this;
        fs.stat(this.filename, function (err, stats) {
            if (err)
                return _this.emit('error', err);
            if (_this.last instanceof Stats) {
                // > The callback listener will be called each time the file is accessed.
                if (_this.last.atime.getTime() != stats.atime.getTime()) {
                    _this.emit('change', stats, _this.last);
                }
            }
            _this.last = stats;
        });
    };
    StatWatcher.prototype.start = function (filename, persistent, interval) {
        var _this = this;
        this.filename = filename;
        fs.stat(filename, function (err, stats) {
            if (err)
                return _this.emit('error', err);
            _this.last = stats;
            _this.interval = setInterval(_this.loop.bind(_this), interval);
        });
    };
    StatWatcher.prototype.stop = function () {
        clearInterval(this.interval);
        this.last = null;
    };
    StatWatcher.map = {};
    return StatWatcher;
}(events_1.EventEmitter));
var watchFileOptionDefaults = {
    persistent: true,
    interval: 5007
};
function watchFile(filename, a, b) {
    if (a === void 0) { a = {}; }
    var vfilename = validPathOrThrow(filename);
    vfilename = pathModule.resolve(vfilename);
    var opts;
    var listener;
    if (typeof a !== 'object') {
        opts = watchFileOptionDefaults;
        listener = a;
    }
    else {
        opts = extend(a, watchFileOptionDefaults);
        listener = b;
    }
    if (typeof listener !== 'function')
        throw new Error('"watchFile()" requires a listener function');
    var watcher = StatWatcher.map[vfilename];
    if (!watcher) {
        watcher = new StatWatcher;
        watcher.start(vfilename, opts.persistent, opts.interval);
        StatWatcher.map[vfilename] = watcher;
    }
    watcher.on('change', listener);
    return watcher;
}
exports.watchFile = watchFile;
function unwatchFile(filename, listener) {
    var vfilename = validPathOrThrow(filename);
    vfilename = pathModule.resolve(vfilename);
    var watcher = StatWatcher.map[vfilename];
    if (!watcher)
        return;
    if (typeof listener === 'function')
        watcher.removeListener('change', listener);
    else
        watcher.removeAllListeners('change');
    if (watcher.listenerCount('change') === 0) {
        watcher.stop();
        delete StatWatcher.map[vfilename];
    }
}
exports.unwatchFile = unwatchFile;
function writeSync(fd, data, a, b, c) {
    validateFd(fd);
    var buf;
    var position;
    // Check which function definition we are working with.
    if (typeof b === 'number') {
        //     writeSync(fd: number, buffer: Buffer, offset: number, length: number, position?: number);
        if (!(data instanceof buffer_1.Buffer))
            throw TypeError('buffer must be instance of Buffer.');
        var offset = a;
        if (typeof offset !== 'number')
            throw TypeError('offset must be an integer');
        var length = b;
        buf = data.slice(offset, offset + length);
        position = c;
    }
    else {
        //     writeSync(fd: number, data: string|Buffer, position?: number, encoding: string = 'utf8');
        var encoding = 'utf8';
        if (b) {
            if (typeof b !== 'string')
                throw TypeError('encoding must be a string');
            encoding = b;
        }
        if (data instanceof buffer_1.Buffer)
            buf = data;
        else if (typeof data === 'string') {
            buf = new buffer_1.Buffer(data, encoding);
        }
        else
            throw TypeError('data must be a Buffer or a string.');
        position = a;
    }
    if (typeof position === 'number') {
        var sres = libjs.lseek(fd, position, 0 /* SET */);
        if (sres < 0)
            throwError(sres, 'write:lseek');
    }
    var res = libjs.write(fd, buf);
    if (res < 0)
        throwError(res, 'write');
}
exports.writeSync = writeSync;
// Wrap synchronous/blocking functions into async ones just to confirm to Node's API.
function useFake(fs) {
    require('./afs-fake')(fs);
}
exports.useFake = useFake;
function useTagg(fs) {
    require('./afs-tagg')(fs);
}
exports.useTagg = useTagg;
function useLibaio(fs) {
    require('./afs-libaio')(fs);
}
exports.useLibaio = useLibaio;
