#pragma once

#include <map>
#include <string>
#include <cstring>
#include <cassert>
#include <iostream>
#include <docopt/docopt.h>

extern const char USAGE[];

class ArgNotFoundException : std::runtime_error {
public:
    ArgNotFoundException(const std::string& msg) : runtime_error(msg) {}
};

class ArgTypeException : std::runtime_error {
public:
    ArgTypeException(const std::string& msg) : runtime_error(msg) {}
};

struct ConfigStruct {
    /**
     * Parses cmd-line arguments
     */
    void parse_cmd_args(int argc, char* argv[]) {
        args = docopt::docopt(
                USAGE,
                { argv + 1, argv + argc },
                true              // show help if requested
            );
        // Uncomment for debugging
        /*for (auto const& arg : args) {
            std::cout << arg.first << ": " << arg.second << std::endl;
        }*/
    }

    bool is_set(const std::string& name) {
        auto res = args.find(name);
        if (res == args.end())
            throw ArgNotFoundException(name);
        if (!res->second.isBool())
            throw ArgTypeException(name);
        return res->second.asBool();
    }

    long get_long(const std::string& name) {
        auto res = args.find(name);
        if (res == args.end())
            throw ArgNotFoundException(name);
        if (!res->second.isLong())
            throw ArgTypeException(name);
        return res->second.asLong();
    }

    std::string get_string(const std::string& name) {
        auto res = args.find(name);
        if (res == args.end())
            throw ArgNotFoundException(name);
        if (!res->second.isString())
            throw ArgTypeException(name);
        return res->second.asString();
    }

    std::vector<std::string> get_strings(const std::string& name) {
        auto res = args.find(name);
        if (res == args.end())
            throw ArgNotFoundException(name);
        if (!res->second.isStringList())
            throw ArgTypeException(name);
        return res->second.asStringList();
    }

private:
    std::map<std::string, docopt::value> args;
};

// Global instance of Config
extern ConfigStruct Config;

