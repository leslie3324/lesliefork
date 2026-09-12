# Java 日志示例

以下示例只用于说明模式，不代表要替换项目已有的 logger 或日志布局。

## 参数化消息

优先使用参数化参数，避免日志级别关闭时提前拼接字符串：

```java
log.info("event=payment_authorized payment_id={} duration_ms={}", paymentId, durationMs);
```

由当前层负责最终失败决策时，将异常作为最后一个参数传入，让 logger 输出堆栈：

```java
log.error("event=payment_authorization_failed payment_id={} error_code={}",
        paymentId, errorCode, exception);
```

这些参数中不能包含原始请求体、Authorization Header、Token、Cookie 或密码。

## 上下文传递

如果服务使用 MDC 或等价机制，应复用已有的请求和 Trace 字段。只有在字段稳定且确实有助于关联时才新增字段，并在创建请求上下文的边界负责清理请求级上下文。

## 捕获并重新抛出

不要在每个层级都打印后再重新抛出：

```java
try {
    return client.fetch(resourceId);
} catch (RemoteException exception) {
    log.error("event=resource_fetch_failed resource_id={}", resourceId, exception);
    throw exception;
}
```

只有当前层增加了可操作上下文，并且外层不会再次打印同一个失败时，才采用这种方式。否则直接传递异常，由真正拥有最终处理权的边界打印。

## 测试

当日志输出属于运维契约时，应捕获结构化事件并断言级别、事件名称、稳定字段和脱敏结果。避免对时间戳、空格或完整渲染行做脆弱断言。
